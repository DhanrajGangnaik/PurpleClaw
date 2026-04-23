from __future__ import annotations

from typing import Any

from dashboards.runtime import render_dashboard
from persistence import list_assets, list_findings, list_remediations, list_telemetry_source_health, list_vulnerability_matches, risk_by_asset
from reports.models import GenerateReportRequest, ReportTemplate
from scanning import get_scan_detail


def render_report_preview(payload: GenerateReportRequest, template: ReportTemplate) -> dict[str, Any]:
    data = _collect_report_data(payload, template)
    sections = [{"name": name, "content": _render_section(name, data)} for name in template.sections]
    return {"title": payload.title, "environment_id": payload.environment_id, "generated_from": payload.generated_from, "sections": sections, "metadata": data["metadata"]}


def _collect_report_data(payload: GenerateReportRequest, template: ReportTemplate) -> dict[str, Any]:
    environment_id = payload.environment_id
    findings = list_findings(environment_id)
    return {
        "template": template.model_dump(mode="json"),
        "assets": [asset.model_dump(mode="json") for asset in list_assets(environment_id)],
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "risky_assets": [asset.model_dump(mode="json") for asset in risk_by_asset(environment_id)],
        "vulnerability_matches": [finding.model_dump(mode="json") for finding in list_vulnerability_matches(environment_id)],
        "remediations": [task.model_dump(mode="json") for task in list_remediations(environment_id)],
        "telemetry_coverage": [item.model_dump(mode="json") for item in list_telemetry_source_health(environment_id)],
        "dashboard": render_dashboard(payload.source_id) if payload.generated_from == "dashboard" and payload.source_id else None,
        "scan": get_scan_detail(payload.source_id) if payload.generated_from == "scan" and payload.source_id else None,
        "metadata": {"generated_from": payload.generated_from, "source_id": payload.source_id},
    }


def _render_section(name: str, data: dict[str, Any]) -> dict[str, Any]:
    renderers = {
        "Executive Summary": render_executive_summary,
        "Environment Overview": render_environment_overview,
        "Key Findings": render_key_findings,
        "Prioritized Risks": render_prioritized_risks,
        "Risky Assets": render_risky_assets,
        "Vulnerability Matches": render_vulnerability_matches,
        "Recommended Remediations": render_recommendations,
        "Recommendations": render_recommendations,
        "Telemetry / Monitoring Coverage": render_telemetry_coverage,
        "Telemetry Coverage": render_telemetry_coverage,
        "Appendix": render_appendix,
    }
    return renderers.get(name, render_appendix)(data)


def render_executive_summary(data: dict[str, Any]) -> dict[str, Any]:
    findings = data["findings"]
    return {
        "summary": "PurpleClaw generated this report using approved, deterministic validation workflows only.",
        "metrics": {
            "asset_count": len(data["assets"]),
            "finding_count": len(findings),
            "critical_findings": sum(1 for finding in findings if finding["severity"] == "critical"),
        },
    }


def render_environment_overview(data: dict[str, Any]) -> dict[str, Any]:
    return {"assets": data["assets"][:5], "telemetry_sources": len(data["telemetry_coverage"]), "dashboard_bound": bool(data["dashboard"])}


def render_key_findings(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["findings"][:8]}


def render_prioritized_risks(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["risky_assets"][:5]}


def render_risky_assets(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["risky_assets"][:5]}


def render_vulnerability_matches(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["vulnerability_matches"][:8]}


def render_recommendations(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["remediations"][:8]}


def render_telemetry_coverage(data: dict[str, Any]) -> dict[str, Any]:
    return {"items": data["telemetry_coverage"]}


def render_appendix(data: dict[str, Any]) -> dict[str, Any]:
    scan = data["scan"].model_dump(mode="json") if data["scan"] is not None else None
    return {"source_metadata": data["metadata"], "dashboard": data["dashboard"], "scan": scan}
