from __future__ import annotations

import ssl
from collections import Counter
from urllib.parse import urlparse

from datasources.pipeline.models import QuerySpec
from datasources.pipeline.query import query_data
from persistence import list_assets, list_findings, list_inventory, list_telemetry_source_health, list_vulnerability_matches
from scanning.models import ScanPolicy, ScanRequest


def run_inventory_match(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    matches = list_vulnerability_matches(request.environment_id)
    if asset is not None:
        matches = [finding for finding in matches if finding.asset_id == asset.id]
    return {
        "title": "Inventory match review",
        "category": "vulnerability",
        "severity": "high" if matches else "low",
        "score": 82 if matches else 18,
        "evidence_summary": f"Curated inventory comparison returned {len(matches)} vulnerability match(es).",
        "details": [finding.title for finding in matches[:5]],
    }


def run_tls_check(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    exposure = asset.exposure if asset else "unknown"
    return {
        "title": "TLS certificate metadata review",
        "category": "assessment",
        "severity": "medium" if "internet" in exposure else "low",
        "score": 64 if "internet" in exposure else 24,
        "evidence_summary": f"Safe TLS review used metadata-only inspection rules with protocol policy {ssl.PROTOCOL_TLS_CLIENT}.",
        "details": {"exposure": exposure, "target_scope": request.target},
    }


def run_service_detection(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    inventory = list_inventory(request.environment_id)
    services = [item.component_name for item in inventory if asset and item.asset_id == asset.id]
    return {
        "title": "Approved service fingerprint summary",
        "category": "service_detection",
        "severity": "low",
        "score": 28,
        "evidence_summary": f"Known approved service inventory: {', '.join(services[:6]) or 'none mapped'}",
        "details": {"service_count": len(services)},
    }


def run_header_analysis(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    parsed = urlparse(f"https://{request.target}" if "://" not in request.target else request.target)
    secure_headers = ["strict-transport-security", "content-security-policy", "x-frame-options"]
    return {
        "title": "HTTP security header review",
        "category": "assessment",
        "severity": "medium",
        "score": 58,
        "evidence_summary": f"Safe header analysis prepared checks for {parsed.netloc or parsed.path} using allowlisted metadata inspection.",
        "details": {"expected_headers": secure_headers},
    }


def run_config_audit(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    telemetry_sources = asset.telemetry_sources if asset else []
    findings = list_findings(request.environment_id)
    related = [finding for finding in findings if asset and finding.asset_id == asset.id]
    return {
        "title": "Configuration audit review",
        "category": "misconfiguration",
        "severity": "medium" if len(telemetry_sources) >= 2 else "high",
        "score": 71 if len(telemetry_sources) < 2 else 55,
        "evidence_summary": f"Stored config and telemetry evidence review found {len(related)} related posture item(s).",
        "details": {"telemetry_sources": telemetry_sources},
    }


def run_exposure_review(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    exposure = asset.exposure if asset else "approved scope"
    severity = "medium" if "internet" in exposure else "low"
    return {
        "title": "Exposure review",
        "category": "exposure",
        "severity": severity,
        "score": 67 if severity == "medium" else 22,
        "evidence_summary": f"Metadata-driven exposure review classified target exposure as {exposure}.",
        "details": {"allowed_network_ranges": policy.allowed_network_ranges},
    }


def run_telemetry_gap_check(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    telemetry_sources = asset.telemetry_sources if asset else []
    coverage = list_telemetry_source_health(request.environment_id)
    query_result = query_data(
        request.environment_id,
        QuerySpec(record_types=["metric", "event"], aggregate="count", group_by=["status"], limit=10),
    )
    severity = "high" if len(telemetry_sources) < 2 else "low"
    return {
        "title": "Telemetry coverage gap check",
        "category": "monitoring_gap",
        "severity": severity,
        "score": 84 if severity == "high" else 25,
        "evidence_summary": f"Monitoring coverage mapped {len(telemetry_sources)} telemetry source(s) and {len(coverage)} environment health record(s).",
        "details": {"pipeline_aggregates": query_result.get("aggregates", [])},
    }


def _resolve_asset(environment_id: str, target: str):
    return next((asset for asset in list_assets(environment_id) if target in {asset.id, asset.name}), None)
