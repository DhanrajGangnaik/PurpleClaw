from __future__ import annotations

from typing import Any


SEVERITY_BASE_SCORES = {
    "critical": 90,
    "high": 70,
    "medium": 45,
    "low": 20,
    "info": 5,
}


def calculate_finding_score(finding: Any, asset_context: Any) -> int:
    """Calculate a deterministic defensive priority score for one finding."""

    severity = _value(getattr(finding, "severity", "info"))
    category = str(getattr(finding, "category", "")).lower()
    exposure = str(getattr(finding, "exposure", "")).lower()
    evidence = str(getattr(finding, "evidence_summary", "")).lower()
    verification = str(getattr(finding, "verification", "")).lower()
    asset_exposure = str(_asset_value(asset_context, "exposure")).lower()
    asset_criticality = str(_asset_value(asset_context, "criticality")).lower()
    telemetry_sources = _asset_value(asset_context, "telemetry_sources") or []

    score = SEVERITY_BASE_SCORES.get(severity, 5)
    if "internet" in asset_exposure or "external" in asset_exposure or "exposed" in exposure or "reachability" in exposure:
        score += 8
    if asset_criticality == "critical" or "critical" in str(_asset_value(asset_context, "environment")).lower():
        score += 7
    if category == "monitoring_gap" or not telemetry_sources:
        score += 6
    if category == "runtime_risk":
        score += 5
    if category == "network_risk":
        score += 5
    if "compensating control" in evidence or "compensating control" in verification:
        score -= 10

    return max(0, min(100, round(score)))


def calculate_asset_risk(asset_id: str, findings: list[Any] | None = None, asset_context: Any | None = None) -> int:
    """Calculate aggregate risk for an asset from its open findings."""

    relevant_findings = [
        finding
        for finding in findings or []
        if getattr(finding, "asset_id", None) == asset_id and getattr(finding, "status", None) != "accepted"
    ]
    if not relevant_findings:
        return 0

    scores = [calculate_finding_score(finding, asset_context) for finding in relevant_findings]
    top_score = max(scores)
    secondary_score = round(sum(sorted(scores, reverse=True)[1:4]) * 0.2)
    return max(0, min(100, top_score + secondary_score))


def rank_findings(findings: list[Any]) -> list[Any]:
    """Return findings sorted by score, severity, and recency priority."""

    severity_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
    return sorted(
        findings,
        key=lambda finding: (
            getattr(finding, "score", 0),
            severity_rank.get(_value(getattr(finding, "severity", "info")), 0),
            str(getattr(finding, "updated_at", "")),
        ),
        reverse=True,
    )


def _asset_value(asset_context: Any, key: str) -> Any:
    if asset_context is None:
        return None
    if isinstance(asset_context, dict):
        return asset_context.get(key)
    return getattr(asset_context, key, None)


def _value(value: Any) -> str:
    return str(getattr(value, "value", value)).lower()
