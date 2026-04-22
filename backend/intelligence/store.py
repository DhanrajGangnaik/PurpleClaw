from __future__ import annotations

from planner.schemas import utc_now
from posture.models import Asset, Finding, FindingSeverity, InventoryRecord

from intelligence.models import IntelIndicator, IntelTrend, IntelligenceUpdateRun, ThreatAdvisory
from intelligence.updater import current_risk_summaries, match_advisories, match_trends, relevant_technologies, reprioritize_findings
from persistence.database import db


_ADVISORIES: dict[str, ThreatAdvisory] = {
    "adv-nginx-2024": ThreatAdvisory(
        advisory_id="adv-nginx-2024",
        source_name="Curated Vendor Advisory",
        title="nginx HTTP/2 exposure review",
        category="reverse_proxy_exposure",
        severity=FindingSeverity.HIGH,
        summary="Review nginx HTTP/2 exposure, access boundaries, and vendor patch state for internet-adjacent reverse proxies.",
        affected_products=["nginx"],
        tags=["nginx", "reverse proxy", "http2"],
    ),
    "adv-openssh-2024": ThreatAdvisory(
        advisory_id="adv-openssh-2024",
        source_name="Curated Vendor Advisory",
        title="OpenSSH remote access hardening review",
        category="remote_access",
        severity=FindingSeverity.HIGH,
        summary="Review OpenSSH patch state, exposed management paths, and agent forwarding controls.",
        affected_products=["openssh"],
        tags=["openssh", "remote access", "management"],
    ),
    "adv-grafana-2024": ThreatAdvisory(
        advisory_id="adv-grafana-2024",
        source_name="Curated Vendor Advisory",
        title="Grafana access control review",
        category="application_security",
        severity=FindingSeverity.MEDIUM,
        summary="Review Grafana authorization boundaries, dashboard sharing, and plugin patch state.",
        affected_products=["grafana"],
        tags=["grafana", "observability"],
    ),
    "adv-kubernetes-2024": ThreatAdvisory(
        advisory_id="adv-kubernetes-2024",
        source_name="Curated Platform Advisory",
        title="Kubernetes node and workload control review",
        category="runtime_risk",
        severity=FindingSeverity.HIGH,
        summary="Review kubelet, container runtime, and privileged workload guardrails.",
        affected_products=["kubernetes", "kubelet", "containerd"],
        tags=["kubernetes", "kubelet", "containerd", "runtime"],
    ),
    "adv-prometheus-2024": ThreatAdvisory(
        advisory_id="adv-prometheus-2024",
        source_name="Curated Vendor Advisory",
        title="Prometheus administrative exposure review",
        category="telemetry_exposure",
        severity=FindingSeverity.MEDIUM,
        summary="Review Prometheus access controls, endpoint exposure, and exporter coverage.",
        affected_products=["prometheus", "node-exporter"],
        tags=["prometheus", "node-exporter", "monitoring"],
    ),
}

_INDICATORS: dict[str, IntelIndicator] = {
    "ind-nginx": IntelIndicator(indicator_id="ind-nginx", source_name="Curated Product Signals", indicator_type="product", value="nginx", confidence="high", notes="Reverse proxy exposure context."),
    "ind-openssh": IntelIndicator(indicator_id="ind-openssh", source_name="Curated Product Signals", indicator_type="product", value="openssh", confidence="high", notes="Remote administration exposure context."),
    "ind-grafana": IntelIndicator(indicator_id="ind-grafana", source_name="Curated Product Signals", indicator_type="product", value="grafana", confidence="medium", notes="Observability application context."),
    "ind-kubernetes": IntelIndicator(indicator_id="ind-kubernetes", source_name="Curated Product Signals", indicator_type="technology", value="kubernetes", confidence="high", notes="Cluster and workload runtime context."),
    "ind-prometheus": IntelIndicator(indicator_id="ind-prometheus", source_name="Curated Product Signals", indicator_type="product", value="prometheus", confidence="medium", notes="Metrics and telemetry exposure context."),
}

_TRENDS: dict[str, IntelTrend] = {
    "trend-reverse-proxy": IntelTrend(
        trend_id="trend-reverse-proxy",
        title="Reverse proxy exposure remains a high-value control point",
        category="reverse_proxy_exposure",
        severity=FindingSeverity.HIGH,
        summary="Internet-adjacent reverse proxies should have strong access policy, patch cadence, and telemetry coverage.",
        affected_technologies=["nginx", "reverse proxy", "gateway"],
    ),
    "trend-auth-abuse": IntelTrend(
        trend_id="trend-auth-abuse",
        title="Authentication abuse signal volume requires fast triage",
        category="auth_abuse",
        severity=FindingSeverity.HIGH,
        summary="Repeated authentication failures should be correlated with identity controls and alert routing.",
        affected_technologies=["openssh", "auth", "identity"],
    ),
    "trend-telemetry-gap": IntelTrend(
        trend_id="trend-telemetry-gap",
        title="Telemetry gaps reduce response confidence",
        category="telemetry_gap",
        severity=FindingSeverity.MEDIUM,
        summary="Missing parser, log, or metrics coverage should raise priority for affected posture findings.",
        affected_technologies=["prometheus", "grafana", "loki", "node-exporter", "monitoring"],
    ),
    "trend-runtime": IntelTrend(
        trend_id="trend-runtime",
        title="Container runtime configuration drift affects workload assurance",
        category="runtime_risk",
        severity=FindingSeverity.HIGH,
        summary="Kubernetes and container runtime risks should be reviewed against privileged workload and node control findings.",
        affected_technologies=["kubernetes", "kubelet", "containerd", "container-runtime"],
    ),
}

_UPDATE_RUNS: list[IntelligenceUpdateRun] = []


def list_advisories() -> list[ThreatAdvisory]:
    return list(_ADVISORIES.values())


def list_indicators() -> list[IntelIndicator]:
    return list(_INDICATORS.values())


def list_trends() -> list[IntelTrend]:
    return list(_TRENDS.values())


def list_update_runs() -> list[IntelligenceUpdateRun]:
    if db.enabled:
        return list(reversed(db.list_records("intelligence_update_runs", IntelligenceUpdateRun)))
    return list(reversed(_UPDATE_RUNS))


def relevant_context(inventory: list[InventoryRecord], assets: list[Asset]) -> tuple[list[ThreatAdvisory], list[IntelTrend]]:
    technologies = relevant_technologies(inventory, assets)
    return match_advisories(list_advisories(), technologies), match_trends(list_trends(), technologies)


def relevant_findings(inventory: list[InventoryRecord], assets: list[Asset], findings: list[Finding]) -> list[Finding]:
    advisories, trends = relevant_context(inventory, assets)
    return reprioritize_findings(findings, advisories, trends)


def intelligence_summary(inventory: list[InventoryRecord], assets: list[Asset], findings: list[Finding]) -> dict[str, object]:
    advisories, trends = relevant_context(inventory, assets)
    reprioritized = reprioritize_findings(findings, advisories, trends)
    last_run = _UPDATE_RUNS[-1] if _UPDATE_RUNS else None
    return {
        "source_health": {
            "status": "ready",
            "source_count": 3,
            "last_update_at": last_run.completed_at if last_run else None,
            "notes": "Source-controlled curated intelligence only.",
        },
        "relevant_advisories_count": len(advisories),
        "current_trends_count": len(trends),
        "reprioritized_findings_count": len(reprioritized),
        "relevant_current_risks": current_risk_summaries(advisories, trends),
    }


def run_update(inventory: list[InventoryRecord], assets: list[Asset], findings: list[Finding]) -> IntelligenceUpdateRun:
    started_at = utc_now()
    advisories, trends = relevant_context(inventory, assets)
    reprioritized = reprioritize_findings(findings, advisories, trends)
    run = IntelligenceUpdateRun(
        run_id=f"intel-run-{len(_UPDATE_RUNS) + 1:04d}",
        started_at=started_at,
        completed_at=utc_now(),
        status="completed",
        advisories_loaded=len(_ADVISORIES),
        indicators_loaded=len(_INDICATORS),
        trends_loaded=len(_TRENDS),
        findings_reprioritized=len(reprioritized),
    )
    _UPDATE_RUNS.append(run)
    if db.enabled:
        db.upsert_many("intelligence_update_runs", [run])
    return run
