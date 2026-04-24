from __future__ import annotations

from datetime import timedelta
from typing import Any

from dashboards.store import get_dashboard
from datasources.pipeline.models import QuerySpec
from datasources.pipeline.query import query_data
from datasources.pipeline.storage import list_records
from datasources.store import list_datasources_by_environment
from persistence import list_findings, list_risky_assets, list_service_health, list_telemetry_summaries, list_vulnerability_matches
from planner.schemas import utc_now


def render_dashboard(dashboard_id: str) -> dict[str, Any] | None:
    dashboard = get_dashboard(dashboard_id)
    if dashboard is None:
        return None

    records = list_records(dashboard.environment_id)
    freshness = _freshness_summary(records)
    widgets = [render_widget(dashboard.environment_id, widget, freshness) for widget in dashboard.widgets]
    return {
        "dashboard_id": dashboard.dashboard_id,
        "environment_id": dashboard.environment_id,
        "name": dashboard.name,
        "description": dashboard.description,
        "layout": dashboard.layout,
        "widgets": widgets,
        "rendered_at": utc_now(),
        "datasource_count": len(list_datasources_by_environment(dashboard.environment_id)),
        "data_freshness": freshness,
    }


def render_widget(environment_id: str, widget: dict[str, Any], freshness: dict[str, Any]) -> dict[str, Any]:
    widget_type = str(widget.get("type", "")).strip()
    resolver = {
        "metric_card": _metric_card,
        "findings_table": _findings_table,
        "risky_assets": _risky_assets,
        "telemetry_summary": _telemetry_summary,
        "vulnerabilities_summary": _vulnerabilities_summary,
        "service_health": _service_health,
        "report_list": _report_list,
        "alerts_summary": _pipeline_summary,
        "signals_summary": _pipeline_summary,
    }.get(widget_type, _unsupported)
    rendered = resolver(environment_id, widget)
    rendered["last_updated"] = freshness.get("latest_observed_at")
    rendered["freshness"] = freshness.get("status")
    return rendered


def _metric_card(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    findings = list_findings(environment_id)
    risk_score = max((finding.score for finding in findings), default=0)
    return {**widget, "data": {"value": risk_score, "caption": "Current environment risk score", "source": "findings"}}


def _findings_table(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    limit = int(widget.get("limit", 5))
    findings = list_findings(environment_id)[:limit]
    return {**widget, "data": [finding.model_dump(mode="json") for finding in findings]}


def _risky_assets(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    limit = int(widget.get("limit", 5))
    return {**widget, "data": [asset.model_dump(mode="json") for asset in list_risky_assets(environment_id)[:limit]]}


def _telemetry_summary(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    summaries = list_telemetry_summaries(environment_id)
    aggregate = query_data(environment_id, QuerySpec(record_types=["metric", "event"], aggregate="count", group_by=["status"], limit=10))
    return {**widget, "data": {"summaries": [summary.model_dump(mode="json") for summary in summaries], "pipeline": aggregate}}


def _vulnerabilities_summary(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    matches = list_vulnerability_matches(environment_id)
    severity_counts: dict[str, int] = {}
    for finding in matches:
        severity_counts[str(finding.severity)] = severity_counts.get(str(finding.severity), 0) + 1
    return {**widget, "data": {"total": len(matches), "severity_distribution": severity_counts, "matches": [finding.model_dump(mode="json") for finding in matches[:5]]}}


def _service_health(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    services = list_service_health(environment_id)
    return {**widget, "data": [service.model_dump(mode="json") for service in services]}


def _report_list(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    from reports import list_reports

    limit = int(widget.get("limit", 5))
    reports = list_reports(environment_id)
    return {**widget, "data": [report.model_dump(mode="json") for report in reports[:limit]]}


def _pipeline_summary(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    data = query_data(environment_id, QuerySpec(record_types=["event"], aggregate="count", group_by=["status"], limit=10))
    return {**widget, "data": data}


def _unsupported(environment_id: str, widget: dict[str, Any]) -> dict[str, Any]:
    return {**widget, "data": {"message": f"Widget type {widget.get('type', 'unknown')} is not executable in runtime v1."}}


def _freshness_summary(records) -> dict[str, Any]:
    latest = records[0].observed_at if records else None
    now = utc_now()
    if latest is None:
        return {"status": "stale", "latest_observed_at": None, "record_count": 0}
    age = now - latest
    status = "fresh" if age <= timedelta(minutes=15) else "stale"
    return {"status": status, "latest_observed_at": latest, "record_count": len(records)}
