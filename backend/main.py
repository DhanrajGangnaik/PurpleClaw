from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Union

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import (
    Token,
    UserCreate,
    UserPublic,
    auth_router,
    get_current_user,
    initialize_users,
    require_admin,
    require_analyst,
    require_any,
)
from audit import AuditMiddleware
from collectors.loki import get_loki_config, get_loki_health
from collectors.prometheus import get_prometheus_config, get_prometheus_health
from dashboards.runtime import render_dashboard
from dashboards import Dashboard, DashboardCreate, DashboardUpdate, get_dashboard, initialize_dashboards, list_dashboards, save_dashboard, update_dashboard
from datasources import (
    DataSource,
    DataSourceCreate,
    DataSourceScheduleRequest,
    DataSourceTestRequest,
    DataSourceTestResult,
    get_datasource,
    ingest_environment_datasources,
    initialize_datasources,
    list_datasources,
    save_datasource,
    test_datasource_connection,
)
from datasources.pipeline import QuerySpec, initialize_pipeline, query_data
from datasources.pipeline import list_records_paginated
from datasources.jobs import DatasourceIngestionJob, get_job, list_jobs
from datasources.jobs.bootstrap import initialize_ingestion_runtime
from datasources.jobs.runtime import disable_datasource_ingestion, run_ingestion_job, schedule_datasource_ingestion
from executor import get_executor
from executor.models import ExecutionResult
from intelligence.store import (
    intelligence_summary,
    list_advisories,
    list_trends,
    list_update_runs as list_intelligence_update_runs,
    relevant_findings as intelligence_relevant_findings,
    run_update as run_intelligence_update,
)
from notifications import (
    WebhookConfig,
    WebhookConfigCreate,
    WebhookEvent,
    create_webhook,
    delete_webhook,
    get_webhook,
    initialize_notifications,
    list_webhooks,
    send_event,
    update_webhook,
)
from persistence import (
    create_environment,
    delete_environment,
    derive_findings,
    discover_assets,
    findings_count_by_severity,
    get_environment,
    get_loki_metrics,
    get_prometheus_metrics,
    get_system_mode,
    initialize_persistence,
    list_automation_runs,
    list_alerts,
    list_assets,
    list_dependencies,
    list_environments,
    list_execution_results,
    list_findings,
    list_findings_for_asset,
    list_incidents,
    list_inventory,
    list_inventory_by_asset,
    list_prioritized_findings,
    list_risky_assets,
    list_security_signals,
    list_service_health,
    list_plans,
    list_policies,
    list_remediations,
    list_remediations_for_finding,
    list_telemetry_source_health,
    list_telemetry_summaries,
    list_vulnerability_matches,
    overview_aggregates,
    primary_environment_id,
    remediation_completion_percentage,
    refresh_posture,
    risk_by_asset,
    run_tracking_cycle,
    run_inventory_match,
    save_execution_result,
    save_plan,
    update_environment,
)
from planner import ValidationResult, validate_exercise_plan
from planner.schemas import ExercisePlan
from posture.models import (
    Alert,
    Asset,
    AutomationRun,
    DependencyStatus,
    Environment,
    Finding,
    IncidentSummary,
    InventoryRecord,
    Policy,
    RemediationTask,
    RiskByAsset,
    SecuritySignal,
    ServiceHealth,
    SystemMode,
    TelemetrySourceHealth,
)
from reports import GenerateReportRequest, GeneratedReport, ReportTemplate, generate_report, get_report, initialize_reports, list_report_templates, list_reports, preview_report
from scanning import (
    ScanDetail,
    ScanPolicy,
    ScanPolicyCreate,
    ScanRunRequest,
    enqueue_scan,
    get_scan_detail,
    initialize_execution_engine,
    initialize_scanning,
    list_scan_policies,
    list_scans,
    save_scan_policy,
)
from scheduler import scheduler
from persistence.database import db


# ── Structured JSON logging ────────────────────────────────────────────────────

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        try:
            msg = json.loads(record.getMessage())
        except (json.JSONDecodeError, TypeError):
            msg = {"message": record.getMessage()}
        payload = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "logger": record.name,
            **msg,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def _configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Suppress noisy uvicorn access logs — keep error logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


_configure_logging()
logger = logging.getLogger("purpleclaw.api")


# ── Rate limiter ───────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)


# ── Request/response models ────────────────────────────────────────────────────

class RestoreRequest(BaseModel):
    filename: str


class EnvironmentCreateRequest(BaseModel):
    name: str
    type: Literal["homelab", "lab", "staging", "production"] | None = None
    description: str | None = None
    status: Literal["active", "inactive"] | None = None


class EnvironmentUpdateRequest(BaseModel):
    name: str
    type: Literal["homelab", "lab", "staging", "production"] = "lab"
    description: str | None = None
    status: Literal["active", "inactive"] = "active"


# ── App factory ────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://localhost:5173").split(",") if o.strip()]

app = FastAPI(
    title="PurpleClaw",
    description="Enterprise security operations platform.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(AuditMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

app.include_router(auth_router)


# ── Startup ────────────────────────────────────────────────────────────────────

@app.on_event("startup")
def startup() -> None:
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "purpleclaw-admin")
    initialize_users(admin_username, admin_password)
    initialize_notifications()
    persistence_status = initialize_persistence()
    initialize_pipeline()
    initialize_datasources()
    initialize_ingestion_runtime()
    initialize_dashboards()
    initialize_scanning()
    initialize_execution_engine()
    initialize_reports()
    scheduler.start()
    logger.info(json.dumps({
        "event": "startup",
        "persistence_configured": persistence_status["configured"],
        "persistence_enabled": persistence_status["enabled"],
        "auth_enabled": os.getenv("AUTH_ENABLED", "true").lower() == "true",
        "admin_username": admin_username,
    }))


# ── Security headers middleware ────────────────────────────────────────────────

@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# ── Request ID middleware ──────────────────────────────────────────────────────

@app.middleware("http")
async def request_id(request: Request, call_next) -> Response:
    import uuid
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


# ── Prometheus metrics ─────────────────────────────────────────────────────────

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    _REQUEST_COUNT = Counter("purpleclaw_requests_total", "Total HTTP requests", ["method", "path", "status"])
    _REQUEST_LATENCY = Histogram("purpleclaw_request_duration_seconds", "HTTP request duration", ["method", "path"])

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start
        path = request.url.path
        if path != "/metrics":
            _REQUEST_COUNT.labels(method=request.method, path=path, status=str(response.status_code)).inc()
            _REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

except ImportError:
    pass


# ── Core routes ────────────────────────────────────────────────────────────────

@app.get("/")
def root() -> dict[str, str]:
    return {"service": "PurpleClaw API", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/platform/health")
def platform_health(_: UserPublic = Depends(require_any)) -> dict[str, object]:
    payload = {
        "api_status": "ok",
        **db.platform_health(scheduler.status(), len(list_environments())),
    }
    logger.info(json.dumps({"event": "platform_health", "backend": payload.get("backend"), "writable": payload.get("writable")}))
    return payload


@app.post("/platform/backup")
def platform_backup(_: UserPublic = Depends(require_admin)) -> dict[str, object]:
    try:
        result = db.backup()
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(json.dumps({"event": "platform_backup", "filename": result["filename"], "size_bytes": result["size_bytes"]}))
    return result


@app.get("/platform/backups")
def platform_backups(_: UserPublic = Depends(require_any)) -> list[dict[str, object]]:
    return db.list_backups()


@app.post("/platform/restore")
def platform_restore(request: RestoreRequest, _: UserPublic = Depends(require_admin)) -> dict[str, object]:
    try:
        result = db.restore(request.filename)
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(json.dumps({"event": "platform_restore", "filename": result["filename"]}))
    return result


# ── Environments ───────────────────────────────────────────────────────────────

@app.get("/environments", response_model=list[Environment])
def environments(_: UserPublic = Depends(require_any)) -> list[Environment]:
    records = list_environments()
    logger.info(json.dumps({"event": "list_environments", "count": len(records)}))
    return records


@app.post("/environments", response_model=Environment, status_code=201)
def environment_create(payload: EnvironmentCreateRequest, _: UserPublic = Depends(require_analyst)) -> Environment:
    try:
        record = create_environment(
            name=payload.name,
            environment_type=payload.type,
            description=payload.description,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(json.dumps({"event": "create_environment_failed", "name": payload.name, "error": str(exc)}))
        raise HTTPException(status_code=500, detail="Failed to create environment") from exc
    logger.info(json.dumps({"event": "create_environment", "environment_id": record.environment_id}))
    return record


@app.get("/environments/{environment_id}", response_model=Environment)
def environment(environment_id: str, _: UserPublic = Depends(require_any)) -> Environment:
    record = get_environment(environment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    return record


@app.put("/environments/{environment_id}", response_model=Environment)
def environment_update(environment_id: str, payload: EnvironmentUpdateRequest, _: UserPublic = Depends(require_analyst)) -> Environment:
    record = update_environment(
        environment_id=environment_id,
        name=payload.name,
        environment_type=payload.type,
        description=payload.description,
        status=payload.status,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    return record


@app.delete("/environments/{environment_id}", status_code=204, response_model=None)
def environment_delete(environment_id: str, _: UserPublic = Depends(require_admin)) -> None:
    record = get_environment(environment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    if not delete_environment(environment_id):
        raise HTTPException(status_code=400, detail="Unable to delete environment")


# ── Integrations ───────────────────────────────────────────────────────────────

@app.get("/integrations/prometheus/config")
def prometheus_config(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_prometheus_config(environment_id or primary_environment_id())


@app.get("/integrations/prometheus/health")
def prometheus_health(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_prometheus_health(environment_id or primary_environment_id())


@app.get("/integrations/prometheus/summary")
def prometheus_summary(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_prometheus_metrics(environment_id)


@app.get("/integrations/loki/config")
def loki_config(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_loki_config(environment_id or primary_environment_id())


@app.get("/integrations/loki/health")
def loki_health(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_loki_health(environment_id or primary_environment_id())


@app.get("/integrations/loki/summary")
def loki_summary(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    return get_loki_metrics(environment_id)


# ── Plans & Executions ─────────────────────────────────────────────────────────

@app.post("/validate-plan", response_model=ValidationResult)
def validate_plan(plan: ExercisePlan, environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> ValidationResult:
    validation = validate_exercise_plan(plan)
    logger.info(json.dumps({"event": "validate_plan", "plan_id": plan.id, "valid": validation.valid, "actor": current_user.username}))
    if validation.valid:
        save_plan(plan, environment_id)
    return validation


@app.post("/execute-stub", response_model=Union[ValidationResult, ExecutionResult])
def execute_stub(plan: ExercisePlan, environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> Union[ValidationResult, ExecutionResult]:
    validation = validate_exercise_plan(plan)
    if not validation.valid:
        return validation
    if not plan.execution_steps:
        return ValidationResult(valid=False, errors=["execution_steps must include at least one step"])
    save_plan(plan, environment_id)
    executor_name = str(plan.execution_steps[0].executor)
    executor_cls = get_executor(executor_name)
    executor = executor_cls()
    result = executor.execute(plan)
    logger.info(json.dumps({"event": "execute_plan", "plan_id": plan.id, "executor": result.executor, "actor": current_user.username}))
    save_execution_result(result, environment_id)
    return result


@app.get("/plans", response_model=list[ExercisePlan])
def plans(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[ExercisePlan]:
    return list_plans(environment_id)


@app.get("/executions", response_model=list[ExecutionResult])
def executions(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[ExecutionResult]:
    return list_execution_results(environment_id)


# ── Posture data ───────────────────────────────────────────────────────────────

@app.get("/system-mode", response_model=SystemMode)
def system_mode(_: UserPublic = Depends(require_any)) -> SystemMode:
    return get_system_mode()


@app.get("/assets", response_model=list[Asset])
def assets(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Asset]:
    return list_assets(environment_id)


@app.get("/assets/risky", response_model=list[RiskByAsset])
def risky_assets(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[RiskByAsset]:
    return list_risky_assets(environment_id)


@app.get("/inventory", response_model=list[InventoryRecord])
def inventory(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[InventoryRecord]:
    return list_inventory(environment_id)


@app.get("/inventory/{asset_id}", response_model=list[InventoryRecord])
def inventory_for_asset(asset_id: str, environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[InventoryRecord]:
    return list_inventory_by_asset(asset_id, environment_id)


@app.get("/vulnerabilities/matches", response_model=list[Finding])
def vulnerability_matches(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Finding]:
    return list_vulnerability_matches(environment_id)


@app.get("/findings", response_model=list[Finding])
def findings(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Finding]:
    return list_findings(environment_id)


@app.get("/findings/prioritized", response_model=list[Finding])
def prioritized_findings(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Finding]:
    return list_prioritized_findings(environment_id)


@app.get("/findings/{asset_id}", response_model=list[Finding])
def findings_for_asset(asset_id: str, environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Finding]:
    return list_findings_for_asset(asset_id, environment_id)


@app.get("/alerts", response_model=list[Alert])
def alerts(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Alert]:
    return list_alerts(environment_id)


@app.get("/signals", response_model=list[SecuritySignal])
def signals(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[SecuritySignal]:
    return list_security_signals(environment_id)


@app.get("/incidents", response_model=list[IncidentSummary])
def incidents(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[IncidentSummary]:
    return list_incidents(environment_id)


@app.get("/service-health", response_model=list[ServiceHealth])
def service_health(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[ServiceHealth]:
    return list_service_health(environment_id)


@app.get("/dependencies", response_model=list[DependencyStatus])
def dependencies(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[DependencyStatus]:
    return list_dependencies(environment_id)


@app.get("/telemetry-sources/health", response_model=list[TelemetrySourceHealth])
def telemetry_sources_health(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[TelemetrySourceHealth]:
    return list_telemetry_source_health(environment_id)


@app.get("/remediations", response_model=list[RemediationTask])
def remediations(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[RemediationTask]:
    return list_remediations(environment_id)


@app.get("/remediations/{finding_id}", response_model=list[RemediationTask])
def remediations_for_finding(finding_id: str, environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[RemediationTask]:
    return list_remediations_for_finding(finding_id, environment_id)


@app.get("/policies", response_model=list[Policy])
def policies(_: UserPublic = Depends(require_any)) -> list[Policy]:
    return list_policies()


# ── Reports ────────────────────────────────────────────────────────────────────

@app.get("/reports", response_model=list[GeneratedReport])
def reports(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[GeneratedReport]:
    return list_reports(environment_id)


@app.get("/report-templates", response_model=list[ReportTemplate])
def report_templates(_: UserPublic = Depends(require_any)) -> list[ReportTemplate]:
    return list_report_templates()


@app.post("/reports/generate", response_model=GeneratedReport)
def reports_generate(request: GenerateReportRequest, current_user: UserPublic = Depends(require_analyst)) -> GeneratedReport:
    try:
        report = generate_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(json.dumps({"event": "generate_report", "report_id": report.report_id, "actor": current_user.username, "status": report.status}))
    if report.status == "ready":
        send_event(WebhookEvent(
            event_type="report.generated",
            environment_id=report.environment_id,
            severity="info",
            title=f"Report generated: {report.title}",
            body=f"Report '{report.title}' is ready for download.",
            metadata={"report_id": report.report_id},
        ))
    return report


@app.post("/reports/preview")
def reports_preview(request: GenerateReportRequest, _: UserPublic = Depends(require_analyst)) -> dict[str, object]:
    try:
        return preview_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/reports/{report_id}", response_model=GeneratedReport)
def report_detail(report_id: str, _: UserPublic = Depends(require_any)) -> GeneratedReport:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@app.get("/reports/{report_id}/download")
def report_download(report_id: str, _: UserPublic = Depends(require_any)) -> FileResponse:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "ready" or not report.file_path:
        raise HTTPException(status_code=400, detail="Report file not available")
    file_path = Path(report.file_path).resolve()
    reports_dir = (Path(__file__).resolve().parent / "data" / "reports").resolve()
    if reports_dir not in file_path.parents or not file_path.exists():
        raise HTTPException(status_code=400, detail="Invalid report path")
    return FileResponse(path=file_path, media_type="application/pdf", filename=file_path.name)


# ── Data sources ───────────────────────────────────────────────────────────────

@app.post("/datasources", response_model=DataSource)
def create_datasource(request: DataSourceCreate, _: UserPublic = Depends(require_analyst)) -> DataSource:
    try:
        record = save_datasource(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(json.dumps({"event": "create_datasource", "datasource_id": record.datasource_id, "type": record.type}))
    return record


@app.get("/datasources", response_model=list[DataSource])
def datasources(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[DataSource]:
    if environment_id:
        ingest_environment_datasources(environment_id)
    return list_datasources(environment_id)


@app.get("/datasources/jobs", response_model=list[DatasourceIngestionJob])
def datasource_jobs(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[DatasourceIngestionJob]:
    return list_jobs(environment_id)


@app.get("/datasources/jobs/{job_id}", response_model=DatasourceIngestionJob)
def datasource_job_detail(job_id: str, _: UserPublic = Depends(require_any)) -> DatasourceIngestionJob:
    record = get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return record


@app.get("/datasources/{datasource_id}", response_model=DataSource)
def datasource_detail(datasource_id: str, _: UserPublic = Depends(require_any)) -> DataSource:
    record = get_datasource(datasource_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    return record


@app.post("/datasources/test", response_model=DataSourceTestResult)
def datasource_test(request: DataSourceTestRequest, _: UserPublic = Depends(require_analyst)) -> DataSourceTestResult:
    try:
        return test_datasource_connection(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/datasources/{datasource_id}/ingest", response_model=DatasourceIngestionJob)
def datasource_ingest(datasource_id: str, _: UserPublic = Depends(require_analyst)) -> DatasourceIngestionJob:
    try:
        return run_ingestion_job(datasource_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/datasources/{datasource_id}/schedule", response_model=DatasourceIngestionJob)
def datasource_schedule_create(datasource_id: str, request: DataSourceScheduleRequest, _: UserPublic = Depends(require_analyst)) -> DatasourceIngestionJob:
    try:
        return schedule_datasource_ingestion(datasource_id, request.trigger_mode, request.interval_seconds, request.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/datasources/{datasource_id}/schedule", response_model=DatasourceIngestionJob)
def datasource_schedule_update(datasource_id: str, request: DataSourceScheduleRequest, _: UserPublic = Depends(require_analyst)) -> DatasourceIngestionJob:
    try:
        return schedule_datasource_ingestion(datasource_id, request.trigger_mode, request.interval_seconds, request.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/datasources/{datasource_id}/schedule/disable", response_model=DatasourceIngestionJob)
def datasource_schedule_disable(datasource_id: str, _: UserPublic = Depends(require_analyst)) -> DatasourceIngestionJob:
    try:
        return disable_datasource_ingestion(datasource_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/datasources/{datasource_id}/records")
def datasource_records(
    datasource_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    record_type: str | None = Query(default=None),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    _: UserPublic = Depends(require_any),
) -> dict[str, object]:
    datasource = get_datasource(datasource_id)
    if datasource is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    parsed_start_at = datetime.fromisoformat(start_at) if start_at else None
    parsed_end_at = datetime.fromisoformat(end_at) if end_at else None
    return list_records_paginated(
        datasource.environment_id,
        datasource_id,
        record_type=record_type,
        start_at=parsed_start_at,
        end_at=parsed_end_at,
        page=page,
        page_size=page_size,
    )


# ── Dashboards ─────────────────────────────────────────────────────────────────

@app.post("/dashboards", response_model=Dashboard)
def create_dashboard(request: DashboardCreate, _: UserPublic = Depends(require_analyst)) -> Dashboard:
    try:
        return save_dashboard(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/dashboards", response_model=list[Dashboard])
def dashboards(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Dashboard]:
    return list_dashboards(environment_id)


@app.get("/dashboards/{dashboard_id}", response_model=Dashboard)
def dashboard_detail(dashboard_id: str, _: UserPublic = Depends(require_any)) -> Dashboard:
    record = get_dashboard(dashboard_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return record


@app.get("/dashboards/{dashboard_id}/render")
def dashboard_render(dashboard_id: str, _: UserPublic = Depends(require_any)) -> dict[str, object]:
    rendered = render_dashboard(dashboard_id)
    if rendered is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    ingest_environment_datasources(str(rendered["environment_id"]))
    rendered = render_dashboard(dashboard_id)
    if rendered is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return rendered


@app.put("/dashboards/{dashboard_id}", response_model=Dashboard)
def dashboard_update(dashboard_id: str, request: DashboardUpdate, _: UserPublic = Depends(require_analyst)) -> Dashboard:
    try:
        record = update_dashboard(dashboard_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return record


# ── Scans ──────────────────────────────────────────────────────────────────────

@app.get("/scan-policies", response_model=list[ScanPolicy])
def scan_policies(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[ScanPolicy]:
    return list_scan_policies(environment_id)


@app.post("/scan-policies", response_model=ScanPolicy)
def create_scan_policy(request: ScanPolicyCreate, _: UserPublic = Depends(require_analyst)) -> ScanPolicy:
    try:
        return save_scan_policy(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/scans", response_model=list[ScanDetail])
def scans(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[ScanDetail]:
    return list_scans(environment_id)


@app.get("/scans/{scan_id}", response_model=ScanDetail)
def scan_detail(scan_id: str, _: UserPublic = Depends(require_any)) -> ScanDetail:
    record = get_scan_detail(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return record


@app.post("/scans/run", response_model=ScanDetail)
def scans_run(request: ScanRunRequest, current_user: UserPublic = Depends(require_analyst)) -> ScanDetail:
    try:
        queued = enqueue_scan(request)
        record = get_scan_detail(queued.scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(json.dumps({"event": "queue_scan", "scan_id": queued.scan_id, "target": request.target, "actor": current_user.username}))
    send_event(WebhookEvent(
        event_type="scan.queued",
        environment_id=request.environment_id,
        severity="info",
        title=f"Scan queued for {request.target}",
        body=f"Scan types: {', '.join(request.scan_types)}",
        metadata={"scan_id": queued.scan_id},
    ))
    return record


# ── Data pipeline ──────────────────────────────────────────────────────────────

@app.post("/data/query")
def data_query(request: QuerySpec, environment_id: str = Query(...), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    ingest_environment_datasources(environment_id)
    return query_data(environment_id, request)


@app.get("/telemetry-summary")
def telemetry_summary(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    summaries = list_telemetry_summaries(environment_id)
    return {
        "summaries": summaries,
        "risk_by_asset": risk_by_asset(environment_id),
        "findings_by_severity": findings_count_by_severity(environment_id),
        "remediation_completion_percentage": remediation_completion_percentage(environment_id),
        "overview_aggregates": overview_aggregates(environment_id),
    }


# ── Intelligence ───────────────────────────────────────────────────────────────

@app.get("/intelligence/summary")
def intelligence_summary_route(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> dict[str, object]:
    active = environment_id or primary_environment_id()
    return intelligence_summary(list_inventory(active), list_assets(active), list_findings(active))


@app.get("/intelligence/advisories")
def intelligence_advisories(_: UserPublic = Depends(require_any)) -> list[object]:
    return list_advisories()


@app.get("/intelligence/trends")
def intelligence_trends(_: UserPublic = Depends(require_any)) -> list[object]:
    return list_trends()


@app.get("/intelligence/relevant-findings", response_model=list[Finding])
def intelligence_relevant_findings_route(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[Finding]:
    active = environment_id or primary_environment_id()
    return intelligence_relevant_findings(list_inventory(active), list_assets(active), list_findings(active))


@app.get("/intelligence/update-runs")
def intelligence_update_runs(_: UserPublic = Depends(require_any)) -> list[object]:
    return list_intelligence_update_runs()


# ── Automation ─────────────────────────────────────────────────────────────────

@app.get("/automation/runs", response_model=list[AutomationRun])
def automation_runs(environment_id: str | None = Query(default=None), _: UserPublic = Depends(require_any)) -> list[AutomationRun]:
    return list_automation_runs(environment_id)


@app.get("/scheduler/status")
def scheduler_status(_: UserPublic = Depends(require_any)) -> dict[str, object]:
    return scheduler.status()


@app.post("/scheduler/run/tracking", response_model=AutomationRun)
def scheduler_run_tracking(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = scheduler.run_now("tracking", lambda: run_tracking_cycle(environment_id))
    logger.info(json.dumps({"event": "scheduler_run_tracking", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/scheduler/run/intelligence")
def scheduler_run_intelligence(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> object:
    active = environment_id or primary_environment_id()
    run = scheduler.run_now("intelligence", lambda: run_intelligence_update(list_inventory(active), list_assets(active), list_findings(active)))
    logger.info(json.dumps({"event": "scheduler_run_intelligence", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/scheduler/run/inventory", response_model=AutomationRun)
def scheduler_run_inventory(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = scheduler.run_now("inventory", lambda: run_inventory_match(environment_id))
    logger.info(json.dumps({"event": "scheduler_run_inventory", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/automation/discover-assets", response_model=AutomationRun)
def automation_discover_assets(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = discover_assets(environment_id)
    logger.info(json.dumps({"event": "discover_assets", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/automation/derive-findings", response_model=AutomationRun)
def automation_derive_findings(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = derive_findings(environment_id)
    logger.info(json.dumps({"event": "derive_findings", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/automation/refresh-posture", response_model=AutomationRun)
def automation_refresh_posture(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = refresh_posture(environment_id)
    logger.info(json.dumps({"event": "refresh_posture", "run_id": run.run_id, "posture_score": run.posture_score, "actor": current_user.username}))
    return run


@app.post("/automation/run-tracking-cycle", response_model=AutomationRun)
def automation_run_tracking_cycle(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = run_tracking_cycle(environment_id)
    logger.info(json.dumps({"event": "run_tracking_cycle", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/automation/run-inventory-match", response_model=AutomationRun)
def automation_run_inventory_match(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> AutomationRun:
    run = run_inventory_match(environment_id)
    logger.info(json.dumps({"event": "run_inventory_match", "run_id": run.run_id, "actor": current_user.username}))
    return run


@app.post("/automation/update-intelligence")
def automation_update_intelligence(environment_id: str | None = Query(default=None), current_user: UserPublic = Depends(require_analyst)) -> object:
    active = environment_id or primary_environment_id()
    run = run_intelligence_update(list_inventory(active), list_assets(active), list_findings(active))
    logger.info(json.dumps({"event": "update_intelligence", "run_id": run.run_id, "actor": current_user.username}))
    return run


# ── Webhook notifications ──────────────────────────────────────────────────────

@app.get("/notifications/webhooks", response_model=list[WebhookConfig])
def get_webhooks(_: UserPublic = Depends(require_admin)) -> list[WebhookConfig]:
    return list_webhooks()


@app.post("/notifications/webhooks", response_model=WebhookConfig, status_code=201)
def create_webhook_endpoint(payload: WebhookConfigCreate, _: UserPublic = Depends(require_admin)) -> WebhookConfig:
    return create_webhook(payload)


@app.get("/notifications/webhooks/{webhook_id}", response_model=WebhookConfig)
def get_webhook_endpoint(webhook_id: str, _: UserPublic = Depends(require_admin)) -> WebhookConfig:
    webhook = get_webhook(webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.put("/notifications/webhooks/{webhook_id}", response_model=WebhookConfig)
def update_webhook_endpoint(webhook_id: str, payload: WebhookConfigCreate, _: UserPublic = Depends(require_admin)) -> WebhookConfig:
    webhook = update_webhook(webhook_id, payload)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@app.delete("/notifications/webhooks/{webhook_id}", status_code=204, response_model=None)
def delete_webhook_endpoint(webhook_id: str, _: UserPublic = Depends(require_admin)) -> None:
    if not delete_webhook(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")


@app.post("/notifications/webhooks/{webhook_id}/test", status_code=202)
def test_webhook_endpoint(webhook_id: str, _: UserPublic = Depends(require_admin)) -> dict[str, str]:
    webhook = get_webhook(webhook_id)
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")
    send_event(WebhookEvent(
        event_type="webhook.test",
        environment_id="test",
        severity="info",
        title="PurpleClaw Webhook Test",
        body="This is a test notification from PurpleClaw.",
        metadata={"webhook_id": webhook_id},
    ))
    return {"status": "dispatched"}
