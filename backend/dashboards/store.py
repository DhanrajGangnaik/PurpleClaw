from __future__ import annotations

from uuid import uuid4

from dashboards.models import Dashboard, DashboardCreate, DashboardUpdate
from persistence.database import db
from persistence.store import get_environment, list_environments
from planner.schemas import utc_now
from templates import SUPPORTED_WIDGET_TYPES


_DASHBOARDS: dict[str, Dashboard] = {}


def initialize_dashboards() -> None:
    if db.enabled:
        for record in db.list_records("dashboards", Dashboard):
            _DASHBOARDS[record.dashboard_id] = record

    for environment in list_environments():
        dashboard_id = f"{environment.environment_id}-executive"
        if dashboard_id not in _DASHBOARDS:
            save_dashboard(
                DashboardCreate(
                    environment_id=environment.environment_id,
                    name="Executive Exposure",
                    description="Default environment summary with findings, telemetry, and reporting context.",
                    layout={"columns": 12, "rowHeight": 96},
                    widgets=[
                        {"widget_id": "w-risk", "type": "metric_card", "title": "Risk Score", "datasource": "inventory"},
                        {"widget_id": "w-findings", "type": "findings_table", "title": "Key Findings", "limit": 5},
                        {"widget_id": "w-assets", "type": "risky_assets", "title": "Risky Assets", "limit": 5},
                        {"widget_id": "w-reports", "type": "report_list", "title": "Reports", "limit": 5},
                    ],
                ),
                dashboard_id=dashboard_id,
            )


def save_dashboard(payload: DashboardCreate, dashboard_id: str | None = None) -> Dashboard:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")
    _validate_widgets(payload.widgets)

    existing = _DASHBOARDS.get(dashboard_id or "")
    record = Dashboard(
        dashboard_id=dashboard_id or f"dash-{uuid4().hex[:12]}",
        environment_id=payload.environment_id,
        name=payload.name,
        description=payload.description,
        layout=payload.layout,
        widgets=payload.widgets,
        created_at=existing.created_at if existing else utc_now(),
        updated_at=utc_now(),
    )
    _DASHBOARDS[record.dashboard_id] = record
    if db.enabled:
        db.upsert_many("dashboards", [record])
    return record


def update_dashboard(dashboard_id: str, payload: DashboardUpdate) -> Dashboard | None:
    existing = _DASHBOARDS.get(dashboard_id)
    if existing is None:
        return None
    _validate_widgets(payload.widgets)
    updated = existing.model_copy(
        update={
            "name": payload.name,
            "description": payload.description,
            "layout": payload.layout,
            "widgets": payload.widgets,
            "updated_at": utc_now(),
        }
    )
    _DASHBOARDS[dashboard_id] = updated
    if db.enabled:
        db.upsert_many("dashboards", [updated])
    return updated


def list_dashboards(environment_id: str | None = None) -> list[Dashboard]:
    records = _DASHBOARDS.values()
    if environment_id:
        records = [dashboard for dashboard in records if dashboard.environment_id == environment_id]
    return sorted(records, key=lambda item: item.updated_at, reverse=True)


def get_dashboard(dashboard_id: str) -> Dashboard | None:
    return _DASHBOARDS.get(dashboard_id)


def _validate_widgets(widgets: list[dict[str, object]]) -> None:
    for widget in widgets:
        widget_type = str(widget.get("type", "")).strip()
        if widget_type not in SUPPORTED_WIDGET_TYPES:
            raise ValueError(f"Unsupported widget type: {widget_type or 'unknown'}")
