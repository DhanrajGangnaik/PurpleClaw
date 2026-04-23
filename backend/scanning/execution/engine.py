from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from persistence import save_tracking_findings
from posture.models import DataSource, Finding, FindingSeverity
from posture.scoring import calculate_finding_score
from planner.schemas import utc_now
from scanning.execution.dispatcher import dispatch_scan, initialize_dispatcher
from scanning.models import ScanRequest, ScanResult, ScanRunRequest
from scanning.store import (
    check_scope,
    get_scan,
    get_scan_policy_for_environment,
    save_scan_request,
    save_scan_result,
)


_EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="purpleclaw-scan")


def initialize_execution_engine() -> None:
    initialize_dispatcher()


def enqueue_scan(payload: ScanRunRequest) -> ScanRequest:
    scan_id = f"scan-{uuid4().hex[:12]}"
    request = ScanRequest(
        scan_id=scan_id,
        environment_id=payload.environment_id,
        target=payload.target,
        target_type=payload.target_type,
        scan_types=sorted(set(payload.scan_types)),
        depth=payload.depth,
        requested_by=payload.requested_by,
        notes=payload.notes,
        status="queued",
    )
    save_scan_request(request)
    save_scan_result(
        ScanResult(
            scan_id=scan_id,
            environment_id=request.environment_id,
            target=request.target,
            findings_created=0,
            summary={"message": "Assessment queued for safe background execution."},
            status="queued",
        )
    )
    _EXECUTOR.submit(process_scan_request, scan_id)
    return request


def process_scan_request(scan_id: str) -> None:
    request = get_scan(scan_id)
    if request is None:
        return

    allowed, message, policy = check_scope(request)
    if not allowed or policy is None:
        blocked_request = request.model_copy(update={"status": "blocked"})
        save_scan_request(blocked_request)
        save_scan_result(
            ScanResult(
                scan_id=scan_id,
                environment_id=request.environment_id,
                target=request.target,
                findings_created=0,
                summary={"message": message, "blocked_by_policy": policy.policy_id if policy else None},
                started_at=utc_now(),
                completed_at=utc_now(),
                status="blocked",
            )
        )
        return

    running_request = request.model_copy(update={"status": "running"})
    save_scan_request(running_request)
    save_scan_result(
        ScanResult(
            scan_id=scan_id,
            environment_id=request.environment_id,
            target=request.target,
            findings_created=0,
            summary={"message": "Assessment is running with approved checks only.", "policy_id": policy.policy_id},
            started_at=utc_now(),
            status="running",
        )
    )

    try:
        rendered = []
        for scan_type in running_request.scan_types:
            allowed, message, latest_policy = check_scope(running_request)
            if not allowed or latest_policy is None:
                raise ValueError(message)
            handler = dispatch_scan(scan_type)
            rendered.append(handler(running_request, latest_policy))

        findings = _build_findings(running_request, rendered)
        save_tracking_findings(findings)
        save_scan_request(running_request.model_copy(update={"status": "completed"}))
        save_scan_result(
            ScanResult(
                scan_id=scan_id,
                environment_id=request.environment_id,
                target=request.target,
                findings_created=len(findings),
                summary={
                    "message": "Approved assessment completed using deterministic safe checks.",
                    "policy_id": policy.policy_id,
                    "scan_types": running_request.scan_types,
                    "generated_findings": rendered,
                },
                started_at=utc_now(),
                completed_at=utc_now(),
                status="completed",
            )
        )
    except Exception as exc:  # noqa: BLE001
        save_scan_request(running_request.model_copy(update={"status": "failed"}))
        save_scan_result(
            ScanResult(
                scan_id=scan_id,
                environment_id=request.environment_id,
                target=request.target,
                findings_created=0,
                summary={"message": f"Assessment failed safely: {exc}", "policy_id": policy.policy_id},
                started_at=utc_now(),
                completed_at=utc_now(),
                status="failed",
            )
        )


def _build_findings(request: ScanRequest, rendered: list[dict[str, object]]) -> list[Finding]:
    asset_id = request.target
    now = utc_now()
    findings: list[Finding] = []
    for index, item in enumerate(rendered, start=1):
        severity = FindingSeverity(str(item.get("severity", "low")).lower())
        finding = Finding(
            id=f"{request.scan_id}-finding-{index:02d}",
            environment_id=request.environment_id,
            asset_id=asset_id,
            title=str(item.get("title", f"Assessment finding {index}")),
            severity=severity,
            category=str(item.get("category", "assessment")),
            status="open",
            exposure=f"assessment result for {request.target}",
            evidence_summary=str(item.get("evidence_summary", "Approved scan execution produced this result.")),
            verification="Review evidence and confirm remediation or acceptance within authorized workflow.",
            confidence="high" if severity in {FindingSeverity.CRITICAL, FindingSeverity.HIGH} else "medium",
            affected_component=str(item.get("category", "assessment")),
            source=DataSource.TRACKING,
            opened_at=now,
            updated_at=now,
        )
        findings.append(finding.model_copy(update={"score": calculate_finding_score(finding, None)}))
    return findings
