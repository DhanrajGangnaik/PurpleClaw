from __future__ import annotations

import ipaddress
from uuid import uuid4

from persistence.database import db
from persistence.store import get_environment, list_assets, list_findings, list_inventory
from scanning.models import ScanDetail, ScanPolicy, ScanPolicyCreate, ScanRequest, ScanResult, ScanRunRequest
from templates import SUPPORTED_SCAN_TYPES


_SCAN_POLICIES: dict[str, ScanPolicy] = {}
_SCAN_REQUESTS: dict[str, ScanRequest] = {}
_SCAN_RESULTS: dict[str, ScanResult] = {}


def initialize_scanning() -> None:
    if db.enabled:
        for record in db.list_records("scan_policies", ScanPolicy):
            _SCAN_POLICIES[record.policy_id] = record
        for record in db.list_records("scan_requests", ScanRequest):
            _SCAN_REQUESTS[record.scan_id] = record
        for record in db.list_records("scan_results", ScanResult):
            _SCAN_RESULTS[record.scan_id] = record

    for environment in {asset.environment_id for asset in list_assets()}:
        policy_id = f"{environment}-default"
        if policy_id in _SCAN_POLICIES:
            continue
        env_assets = list_assets(environment)
        env_inventory = list_inventory(environment)
        allowed_targets = sorted(
            {asset.id for asset in env_assets}
            | {asset.name for asset in env_assets}
            | {item.component_name for item in env_inventory}
        )
        network_ranges = {
            "homelab": ["10.10.0.0/24"],
            "lab": ["10.20.0.0/24"],
            "staging": ["10.30.0.0/24"],
            "production": ["10.40.0.0/24"],
        }
        save_scan_policy(
            ScanPolicyCreate(
                environment_id=environment,
                name="Approved Baseline Policy",
                allowed_targets=allowed_targets,
                allowed_network_ranges=network_ranges.get(environment, []),
                allowed_scan_types=sorted(SUPPORTED_SCAN_TYPES),
                max_depth="standard",
                enabled=True,
            ),
            policy_id=policy_id,
        )


def save_scan_policy(payload: ScanPolicyCreate, policy_id: str | None = None) -> ScanPolicy:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")
    invalid_types = sorted(set(payload.allowed_scan_types) - SUPPORTED_SCAN_TYPES)
    if invalid_types:
        raise ValueError(f"Unsupported scan types in policy: {', '.join(invalid_types)}")

    record = ScanPolicy(
        policy_id=policy_id or f"policy-{uuid4().hex[:12]}",
        environment_id=payload.environment_id,
        name=payload.name,
        allowed_targets=sorted(set(payload.allowed_targets)),
        allowed_network_ranges=sorted(set(payload.allowed_network_ranges)),
        allowed_scan_types=sorted(set(payload.allowed_scan_types)),
        max_depth=payload.max_depth,
        enabled=payload.enabled,
    )
    _SCAN_POLICIES[record.policy_id] = record
    if db.enabled:
        db.upsert_many("scan_policies", [record])
    return record


def list_scan_policies(environment_id: str | None = None) -> list[ScanPolicy]:
    records = _SCAN_POLICIES.values()
    if environment_id:
        records = [policy for policy in records if policy.environment_id == environment_id]
    return sorted(records, key=lambda item: item.name.lower())


def get_scan_policy(policy_id: str) -> ScanPolicy | None:
    return _SCAN_POLICIES.get(policy_id)


def get_scan_policy_for_environment(environment_id: str) -> ScanPolicy | None:
    return next((item for item in list_scan_policies(environment_id) if item.enabled), None)


def save_scan_request(record: ScanRequest) -> ScanRequest:
    _SCAN_REQUESTS[record.scan_id] = record
    if db.enabled:
        db.upsert_many("scan_requests", [record])
    return record


def save_scan_result(record: ScanResult) -> ScanResult:
    _SCAN_RESULTS[record.scan_id] = record
    if db.enabled:
        db.upsert_many("scan_results", [record])
    return record


def list_scans(environment_id: str | None = None) -> list[ScanDetail]:
    requests = _SCAN_REQUESTS.values()
    if environment_id:
        requests = [item for item in requests if item.environment_id == environment_id]
    details: list[ScanDetail] = []
    for item in sorted(requests, key=lambda item: item.requested_at, reverse=True):
        detail = get_scan_detail(item.scan_id)
        if detail is not None:
            details.append(detail)
    return details


def get_scan(scan_id: str) -> ScanRequest | None:
    return _SCAN_REQUESTS.get(scan_id)


def get_scan_result(scan_id: str) -> ScanResult | None:
    return _SCAN_RESULTS.get(scan_id)


def get_scan_detail(scan_id: str) -> ScanDetail | None:
    request = get_scan(scan_id)
    if request is None:
        return None
    result = get_scan_result(scan_id)
    return ScanDetail(
        request=request,
        result=result,
        related_findings=_related_findings(request.environment_id, request.target, request.target_type),
    )


def check_scope(record: ScanRequest) -> tuple[bool, str, ScanPolicy | None]:
    policy = get_scan_policy_for_environment(record.environment_id)
    if policy is None:
        return False, "No enabled scan policy found for this environment", None
    if any(scan_type not in policy.allowed_scan_types for scan_type in record.scan_types):
        return False, "Selected scan type is not approved by policy", policy
    if policy.max_depth == "light" and record.depth == "standard":
        return False, "Requested depth exceeds policy maximum", policy
    if not _target_in_scope(record, policy):
        return False, "Target is not approved for this environment and policy scope", policy
    return True, "approved", policy


def build_scan_request(payload: ScanRunRequest) -> ScanRequest:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")
    if not payload.scan_types:
        raise ValueError("At least one approved scan type must be selected")
    invalid_types = sorted(set(payload.scan_types) - SUPPORTED_SCAN_TYPES)
    if invalid_types:
        raise ValueError(f"Unsupported scan types requested: {', '.join(invalid_types)}")
    return ScanRequest(
        scan_id=f"scan-{uuid4().hex[:12]}",
        environment_id=payload.environment_id,
        target=payload.target,
        target_type=payload.target_type,
        scan_types=sorted(set(payload.scan_types)),
        depth=payload.depth,
        requested_by=payload.requested_by,
        notes=payload.notes,
        status="queued",
    )


def _target_in_scope(record: ScanRequest, policy: ScanPolicy) -> bool:
    target = record.target.strip()
    env_assets = list_assets(record.environment_id)
    env_inventory = list_inventory(record.environment_id)

    if target in policy.allowed_targets:
        return True
    if record.target_type == "asset":
        return any(target in {asset.id, asset.name} for asset in env_assets) and target in policy.allowed_targets
    if record.target_type == "hostname":
        return any(asset.name == target for asset in env_assets) and target in policy.allowed_targets
    if record.target_type == "service":
        return any(item.component_name == target for item in env_inventory) and target in policy.allowed_targets
    if record.target_type == "ip":
        try:
            ip = ipaddress.ip_address(target)
        except ValueError:
            return False
        return any(ip in ipaddress.ip_network(network, strict=False) for network in policy.allowed_network_ranges)
    return False


def _related_findings(environment_id: str, target: str, target_type: str) -> list[dict[str, object]]:
    env_findings = list_findings(environment_id)
    if target_type in {"asset", "hostname"}:
        asset = next((item for item in list_assets(environment_id) if target in {item.id, item.name}), None)
        if asset is not None:
            env_findings = [finding for finding in env_findings if finding.asset_id == asset.id]
    return [
        {
            "id": finding.id,
            "title": finding.title,
            "severity": str(finding.severity),
            "score": finding.score,
            "status": finding.status,
        }
        for finding in env_findings[:10]
    ]
