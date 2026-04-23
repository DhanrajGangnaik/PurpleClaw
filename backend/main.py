import logging
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

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


class RestoreRequest(BaseModel):
    filename: str


class EnvironmentCreateRequest(BaseModel):
    name: str
    type: str
    description: str
    status: str = "active"


class EnvironmentUpdateRequest(BaseModel):
    name: str
    type: str
    description: str
    status: str

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PurpleClaw",
    description="Open-source AI-assisted purple-team validation platform.",
    version="0.1.0",
)


@app.on_event("startup")
def startup() -> None:
    persistence_status = initialize_persistence()
    initialize_pipeline()
    initialize_datasources()
    initialize_ingestion_runtime()
    initialize_dashboards()
    initialize_scanning()
    initialize_execution_engine()
    initialize_reports()
    scheduler.start()
    logger.info(
        "event=startup persistence_configured=%s persistence_enabled=%s",
        str(persistence_status["configured"]).lower(),
        str(persistence_status["enabled"]).lower(),
    )


@app.get("/")
def root() -> dict[str, str]:
    """Return basic service information."""
    return {
        "service": "PurpleClaw API",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Return health status for the API."""
    return {"status": "ok"}


@app.get("/platform/health")
def platform_health() -> dict[str, object]:
    """Return API, persistence, and scheduler health."""
    payload = {
        "api_status": "ok",
        **db.platform_health(scheduler.status(), len(list_environments())),
    }
    logger.info(
        "event=platform_health backend=%s connection_status=%s writable=%s",
        payload.get("backend"),
        payload.get("connection_status"),
        str(payload.get("writable")).lower(),
    )
    return payload


@app.post("/platform/backup")
def platform_backup() -> dict[str, object]:
    """Create an explicit SQLite database backup."""
    try:
        result = db.backup()
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=platform_backup filename=%s size_bytes=%s", result["filename"], result["size_bytes"])
    return result


@app.get("/platform/backups")
def platform_backups() -> list[dict[str, object]]:
    """Return available SQLite database backups."""
    backups = db.list_backups()
    logger.info("event=platform_backups count=%d", len(backups))
    return backups


@app.post("/platform/restore")
def platform_restore(request: RestoreRequest) -> dict[str, object]:
    """Restore the embedded SQLite database from an explicit backup filename."""
    try:
        result = db.restore(request.filename)
    except NotImplementedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=platform_restore filename=%s restored=true", result["filename"])
    return result


@app.get("/environments", response_model=list[Environment])
def environments() -> list[Environment]:
    """Return configured PurpleClaw environments."""
    records = list_environments()
    logger.info("event=list_environments count=%d primary=%s", len(records), primary_environment_id())
    return records


@app.post("/environments", response_model=Environment, status_code=201)
def environment_create(payload: EnvironmentCreateRequest) -> Environment:
    """Create one managed PurpleClaw environment."""

    record = create_environment(
        name=payload.name,
        environment_type=payload.type,
        description=payload.description,
        status=payload.status,
    )
    logger.info("event=create_environment environment_id=%s", record.environment_id)
    return record


@app.get("/environments/{environment_id}", response_model=Environment)
def environment(environment_id: str) -> Environment:
    """Return one configured PurpleClaw environment."""
    record = get_environment(environment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    logger.info("event=get_environment environment_id=%s", environment_id)
    return record


@app.put("/environments/{environment_id}", response_model=Environment)
def environment_update(environment_id: str, payload: EnvironmentUpdateRequest) -> Environment:
    """Update one managed PurpleClaw environment."""

    record = update_environment(
        environment_id=environment_id,
        name=payload.name,
        environment_type=payload.type,
        description=payload.description,
        status=payload.status,
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    logger.info("event=update_environment environment_id=%s", environment_id)
    return record


@app.delete("/environments/{environment_id}", status_code=204)
def environment_delete(environment_id: str) -> None:
    """Delete one managed PurpleClaw environment."""

    record = get_environment(environment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    if not delete_environment(environment_id):
        raise HTTPException(status_code=400, detail="At least one environment must remain")
    logger.info("event=delete_environment environment_id=%s", environment_id)


@app.get("/integrations/prometheus/config")
def prometheus_config(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return read-only Prometheus connector settings."""
    config = get_prometheus_config(environment_id or primary_environment_id())
    logger.info("event=prometheus_config environment_id=%s enabled=%s", config["environment_id"], str(config["enabled"]).lower())
    return config


@app.get("/integrations/prometheus/health")
def prometheus_health(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return Prometheus API reachability for one environment."""
    health = get_prometheus_health(environment_id or primary_environment_id())
    logger.info("event=prometheus_health environment_id=%s status=%s", health["environment_id"], health["status"])
    return health


@app.get("/integrations/prometheus/summary")
def prometheus_summary(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return read-only Prometheus target and node telemetry rollups."""
    summary = get_prometheus_metrics(environment_id)
    logger.info("event=prometheus_summary environment_id=%s", summary["environment_id"])
    return summary


@app.get("/integrations/loki/config")
def loki_config(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return read-only Loki connector settings."""
    config = get_loki_config(environment_id or primary_environment_id())
    logger.info("event=loki_config environment_id=%s enabled=%s", config["environment_id"], str(config["enabled"]).lower())
    return config


@app.get("/integrations/loki/health")
def loki_health(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return Loki API reachability for one environment."""
    health = get_loki_health(environment_id or primary_environment_id())
    logger.info("event=loki_health environment_id=%s status=%s", health["environment_id"], health["status"])
    return health


@app.get("/integrations/loki/summary")
def loki_summary(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return read-only Loki log telemetry rollups."""
    summary = get_loki_metrics(environment_id)
    logger.info("event=loki_summary environment_id=%s", summary["environment_id"])
    return summary


@app.post("/validate-plan", response_model=ValidationResult)
def validate_plan(plan: ExercisePlan, environment_id: str | None = Query(default=None)) -> ValidationResult:
    """Validate an exercise plan without executing it."""
    validation = validate_exercise_plan(plan)

    logger.info(
        "event=validate_plan plan_id=%s valid=%s errors_count=%d",
        plan.id,
        str(validation.valid).lower(),
        len(validation.errors),
    )

    if validation.valid:
        save_plan(plan, environment_id)

    return validation


@app.post("/execute-stub", response_model=Union[ValidationResult, ExecutionResult])
def execute_stub(plan: ExercisePlan, environment_id: str | None = Query(default=None)) -> Union[ValidationResult, ExecutionResult]:
    """Validate a plan and return a safe stub execution result."""
    validation = validate_exercise_plan(plan)

    if not validation.valid:
        logger.info(
            "event=execute_plan plan_id=%s valid=false",
            plan.id,
        )
        return validation

    if not plan.execution_steps:
        logger.info(
            "event=execute_plan plan_id=%s valid=false",
            plan.id,
        )
        return ValidationResult(
            valid=False,
            errors=["execution_steps must include at least one step"],
        )

    save_plan(plan, environment_id)

    executor_name = str(plan.execution_steps[0].executor)
    executor_cls = get_executor(executor_name)
    executor = executor_cls()
    result = executor.execute(plan)

    logger.info("event=execute_plan plan_id=%s executor=%s execution_id=%s valid=true", plan.id, result.executor, result.execution_id)

    save_execution_result(result, environment_id)
    return result


@app.get("/plans", response_model=list[ExercisePlan])
def plans(environment_id: str | None = Query(default=None)) -> list[ExercisePlan]:
    """Return persisted exercise plans."""
    return list_plans(environment_id)


@app.get("/executions", response_model=list[ExecutionResult])
def executions(environment_id: str | None = Query(default=None)) -> list[ExecutionResult]:
    """Return persisted stub execution results."""
    return list_execution_results(environment_id)


@app.get("/system-mode", response_model=SystemMode)
def system_mode() -> SystemMode:
    """Return the active posture data mode."""
    mode = get_system_mode()
    logger.info(
        "event=system_mode mode=%s tracking_enabled=%s",
        mode.mode,
        str(mode.tracking_enabled).lower(),
    )
    return mode


@app.get("/assets", response_model=list[Asset])
def assets(environment_id: str | None = Query(default=None)) -> list[Asset]:
    """Return tracked defensive assets."""
    records = list_assets(environment_id)
    logger.info("event=list_assets environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/assets/risky", response_model=list[RiskByAsset])
def risky_assets(environment_id: str | None = Query(default=None)) -> list[RiskByAsset]:
    """Return assets sorted by aggregate defensive risk score."""
    records = list_risky_assets(environment_id)
    logger.info("event=list_risky_assets environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/inventory", response_model=list[InventoryRecord])
def inventory(environment_id: str | None = Query(default=None)) -> list[InventoryRecord]:
    """Return approved package and service inventory records."""
    records = list_inventory(environment_id)
    logger.info("event=list_inventory environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/inventory/{asset_id}", response_model=list[InventoryRecord])
def inventory_for_asset(asset_id: str, environment_id: str | None = Query(default=None)) -> list[InventoryRecord]:
    """Return approved inventory records for one asset."""
    records = list_inventory_by_asset(asset_id, environment_id)
    logger.info("event=list_inventory_by_asset asset_id=%s environment_id=%s count=%d", asset_id, environment_id or primary_environment_id(), len(records))
    return records


@app.get("/vulnerabilities/matches", response_model=list[Finding])
def vulnerability_matches(environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return seeded CVE matches derived from approved inventory."""
    records = list_vulnerability_matches(environment_id)
    logger.info("event=list_vulnerability_matches environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/findings", response_model=list[Finding])
def findings(environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return defensive posture findings."""
    records = list_findings(environment_id)
    logger.info("event=list_findings environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/findings/prioritized", response_model=list[Finding])
def prioritized_findings(environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return defensive posture findings sorted by risk score."""
    records = list_prioritized_findings(environment_id)
    logger.info("event=list_prioritized_findings environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/findings/{asset_id}", response_model=list[Finding])
def findings_for_asset(asset_id: str, environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return defensive posture findings for one asset."""
    records = list_findings_for_asset(asset_id, environment_id)
    logger.info("event=list_findings_for_asset asset_id=%s environment_id=%s count=%d", asset_id, environment_id or primary_environment_id(), len(records))
    return records


@app.get("/alerts", response_model=list[Alert])
def alerts(environment_id: str | None = Query(default=None)) -> list[Alert]:
    """Return read-only SOC and NOC alerts."""
    records = list_alerts(environment_id)
    logger.info("event=list_alerts environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/signals", response_model=list[SecuritySignal])
def signals(environment_id: str | None = Query(default=None)) -> list[SecuritySignal]:
    """Return correlation-ready security signals."""
    records = list_security_signals(environment_id)
    logger.info("event=list_security_signals environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/incidents", response_model=list[IncidentSummary])
def incidents(environment_id: str | None = Query(default=None)) -> list[IncidentSummary]:
    """Return investigation-friendly incident summaries."""
    records = list_incidents(environment_id)
    logger.info("event=list_incidents environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/service-health", response_model=list[ServiceHealth])
def service_health(environment_id: str | None = Query(default=None)) -> list[ServiceHealth]:
    """Return read-only service health records."""
    records = list_service_health(environment_id)
    logger.info("event=list_service_health environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/dependencies", response_model=list[DependencyStatus])
def dependencies(environment_id: str | None = Query(default=None)) -> list[DependencyStatus]:
    """Return read-only dependency status records."""
    records = list_dependencies(environment_id)
    logger.info("event=list_dependencies environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/telemetry-sources/health", response_model=list[TelemetrySourceHealth])
def telemetry_sources_health(environment_id: str | None = Query(default=None)) -> list[TelemetrySourceHealth]:
    """Return telemetry source health records."""
    records = list_telemetry_source_health(environment_id)
    logger.info("event=list_telemetry_source_health environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/remediations", response_model=list[RemediationTask])
def remediations(environment_id: str | None = Query(default=None)) -> list[RemediationTask]:
    """Return defensive remediation tasks."""
    records = list_remediations(environment_id)
    logger.info("event=list_remediations environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/remediations/{finding_id}", response_model=list[RemediationTask])
def remediations_for_finding(finding_id: str, environment_id: str | None = Query(default=None)) -> list[RemediationTask]:
    """Return remediation tasks for one finding."""
    records = list_remediations_for_finding(finding_id, environment_id)
    logger.info("event=list_remediations_for_finding finding_id=%s environment_id=%s count=%d", finding_id, environment_id or primary_environment_id(), len(records))
    return records


@app.get("/policies", response_model=list[Policy])
def policies() -> list[Policy]:
    """Return defensive posture policies."""
    records = list_policies()
    logger.info("event=list_policies count=%d", len(records))
    return records


@app.get("/reports", response_model=list[GeneratedReport])
def reports(environment_id: str | None = Query(default=None)) -> list[GeneratedReport]:
    """Return generated posture reports."""
    records = list_reports(environment_id)
    logger.info("event=list_reports environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.get("/report-templates", response_model=list[ReportTemplate])
def report_templates() -> list[ReportTemplate]:
    records = list_report_templates()
    logger.info("event=list_report_templates count=%d", len(records))
    return records


@app.post("/reports/generate", response_model=GeneratedReport)
def reports_generate(request: GenerateReportRequest) -> GeneratedReport:
    try:
        report = generate_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=generate_report report_id=%s environment_id=%s status=%s", report.report_id, report.environment_id, report.status)
    return report


@app.post("/reports/preview")
def reports_preview(request: GenerateReportRequest) -> dict[str, object]:
    try:
        payload = preview_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=preview_report environment_id=%s generated_from=%s", request.environment_id, request.generated_from)
    return payload


@app.get("/reports/{report_id}", response_model=GeneratedReport)
def report_detail(report_id: str) -> GeneratedReport:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    logger.info("event=get_report report_id=%s", report_id)
    return report


@app.get("/reports/{report_id}/download")
def report_download(report_id: str) -> FileResponse:
    report = get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "ready" or not report.file_path:
        raise HTTPException(status_code=400, detail="Report file is not available")
    file_path = Path(report.file_path).resolve()
    reports_dir = (Path(__file__).resolve().parent / "data" / "reports").resolve()
    if reports_dir not in file_path.parents or not file_path.exists():
        raise HTTPException(status_code=400, detail="Invalid report path")
    logger.info("event=download_report report_id=%s", report_id)
    return FileResponse(path=file_path, media_type="application/pdf", filename=file_path.name)


@app.post("/datasources", response_model=DataSource)
def create_datasource(request: DataSourceCreate) -> DataSource:
    try:
        record = save_datasource(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=create_datasource datasource_id=%s environment_id=%s type=%s", record.datasource_id, record.environment_id, record.type)
    return record


@app.get("/datasources", response_model=list[DataSource])
def datasources(environment_id: str | None = Query(default=None)) -> list[DataSource]:
    if environment_id:
        ingest_environment_datasources(environment_id)
    records = list_datasources(environment_id)
    logger.info("event=list_datasources environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.get("/datasources/jobs", response_model=list[DatasourceIngestionJob])
def datasource_jobs(environment_id: str | None = Query(default=None)) -> list[DatasourceIngestionJob]:
    records = list_jobs(environment_id)
    logger.info("event=list_datasource_jobs environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.get("/datasources/jobs/{job_id}", response_model=DatasourceIngestionJob)
def datasource_job_detail(job_id: str) -> DatasourceIngestionJob:
    record = get_job(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Datasource ingestion job not found")
    logger.info("event=get_datasource_job job_id=%s", job_id)
    return record


@app.get("/datasources/{datasource_id}", response_model=DataSource)
def datasource_detail(datasource_id: str) -> DataSource:
    record = get_datasource(datasource_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    logger.info("event=get_datasource datasource_id=%s", datasource_id)
    return record


@app.post("/datasources/test", response_model=DataSourceTestResult)
def datasource_test(request: DataSourceTestRequest) -> DataSourceTestResult:
    try:
        result = test_datasource_connection(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=test_datasource environment_id=%s type=%s ok=%s", request.environment_id, request.type, str(result.ok).lower())
    return result


@app.post("/datasources/{datasource_id}/ingest", response_model=DatasourceIngestionJob)
def datasource_ingest(datasource_id: str) -> DatasourceIngestionJob:
    try:
        record = run_ingestion_job(datasource_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=ingest_datasource datasource_id=%s status=%s records_ingested=%d", datasource_id, record.status, record.records_ingested)
    return record


@app.post("/datasources/{datasource_id}/schedule", response_model=DatasourceIngestionJob)
def datasource_schedule_create(datasource_id: str, request: DataSourceScheduleRequest) -> DatasourceIngestionJob:
    try:
        record = schedule_datasource_ingestion(datasource_id, request.trigger_mode, request.interval_seconds, request.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=schedule_datasource datasource_id=%s trigger_mode=%s enabled=%s", datasource_id, request.trigger_mode, str(request.enabled).lower())
    return record


@app.put("/datasources/{datasource_id}/schedule", response_model=DatasourceIngestionJob)
def datasource_schedule_update(datasource_id: str, request: DataSourceScheduleRequest) -> DatasourceIngestionJob:
    try:
        record = schedule_datasource_ingestion(datasource_id, request.trigger_mode, request.interval_seconds, request.enabled)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=update_datasource_schedule datasource_id=%s trigger_mode=%s enabled=%s", datasource_id, request.trigger_mode, str(request.enabled).lower())
    return record


@app.post("/datasources/{datasource_id}/schedule/disable", response_model=DatasourceIngestionJob)
def datasource_schedule_disable(datasource_id: str) -> DatasourceIngestionJob:
    try:
        record = disable_datasource_ingestion(datasource_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=disable_datasource_schedule datasource_id=%s", datasource_id)
    return record


@app.get("/datasources/{datasource_id}/records")
def datasource_records(
    datasource_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    record_type: str | None = Query(default=None),
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
) -> dict[str, object]:
    datasource = get_datasource(datasource_id)
    if datasource is None:
        raise HTTPException(status_code=404, detail="Data source not found")
    parsed_start_at = datetime.fromisoformat(start_at) if start_at else None
    parsed_end_at = datetime.fromisoformat(end_at) if end_at else None
    payload = list_records_paginated(
        datasource.environment_id,
        datasource_id,
        record_type=record_type,
        start_at=parsed_start_at,
        end_at=parsed_end_at,
        page=page,
        page_size=page_size,
    )
    logger.info("event=list_datasource_records datasource_id=%s page=%d count=%d", datasource_id, page, len(payload["items"]))
    return payload


@app.post("/dashboards", response_model=Dashboard)
def create_dashboard(request: DashboardCreate) -> Dashboard:
    try:
        record = save_dashboard(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=create_dashboard dashboard_id=%s environment_id=%s", record.dashboard_id, record.environment_id)
    return record


@app.get("/dashboards", response_model=list[Dashboard])
def dashboards(environment_id: str | None = Query(default=None)) -> list[Dashboard]:
    records = list_dashboards(environment_id)
    logger.info("event=list_dashboards environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.get("/dashboards/{dashboard_id}", response_model=Dashboard)
def dashboard_detail(dashboard_id: str) -> Dashboard:
    record = get_dashboard(dashboard_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    logger.info("event=get_dashboard dashboard_id=%s", dashboard_id)
    return record


@app.get("/dashboards/{dashboard_id}/render")
def dashboard_render(dashboard_id: str) -> dict[str, object]:
    rendered = render_dashboard(dashboard_id)
    if rendered is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    ingest_environment_datasources(str(rendered["environment_id"]))
    rendered = render_dashboard(dashboard_id)
    logger.info("event=render_dashboard dashboard_id=%s widgets=%d", dashboard_id, len(rendered["widgets"]))
    return rendered


@app.put("/dashboards/{dashboard_id}", response_model=Dashboard)
def dashboard_update(dashboard_id: str, request: DashboardUpdate) -> Dashboard:
    try:
        record = update_dashboard(dashboard_id, request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    logger.info("event=update_dashboard dashboard_id=%s", dashboard_id)
    return record


@app.get("/scan-policies", response_model=list[ScanPolicy])
def scan_policies(environment_id: str | None = Query(default=None)) -> list[ScanPolicy]:
    records = list_scan_policies(environment_id)
    logger.info("event=list_scan_policies environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.post("/scan-policies", response_model=ScanPolicy)
def create_scan_policy(request: ScanPolicyCreate) -> ScanPolicy:
    try:
        record = save_scan_policy(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=create_scan_policy policy_id=%s environment_id=%s", record.policy_id, record.environment_id)
    return record


@app.get("/scans", response_model=list[ScanDetail])
def scans(environment_id: str | None = Query(default=None)) -> list[ScanDetail]:
    records = list_scans(environment_id)
    logger.info("event=list_scans environment_id=%s count=%d", environment_id or "all", len(records))
    return records


@app.get("/scans/{scan_id}", response_model=ScanDetail)
def scan_detail(scan_id: str) -> ScanDetail:
    record = get_scan_detail(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    logger.info("event=get_scan scan_id=%s", scan_id)
    return record


@app.post("/scans/run", response_model=ScanDetail)
def scans_run(request: ScanRunRequest) -> ScanDetail:
    try:
        queued = enqueue_scan(request)
        record = get_scan_detail(queued.scan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("event=queue_scan scan_id=%s environment_id=%s status=%s", record.request.scan_id, record.request.environment_id, record.request.status)
    return record


@app.post("/data/query")
def data_query(request: QuerySpec, environment_id: str = Query(...)) -> dict[str, object]:
    ingest_environment_datasources(environment_id)
    payload = query_data(environment_id, request)
    logger.info("event=query_data environment_id=%s count=%s", environment_id, payload.get("count"))
    return payload


@app.get("/telemetry-summary")
def telemetry_summary(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return telemetry summaries and defensive posture helper metrics."""
    summaries = list_telemetry_summaries(environment_id)
    payload = {
        "summaries": summaries,
        "risk_by_asset": risk_by_asset(environment_id),
        "findings_by_severity": findings_count_by_severity(environment_id),
        "remediation_completion_percentage": remediation_completion_percentage(environment_id),
        "overview_aggregates": overview_aggregates(environment_id),
    }
    logger.info("event=telemetry_summary environment_id=%s summaries=%d", environment_id or primary_environment_id(), len(summaries))
    return payload


@app.get("/intelligence/summary")
def intelligence_summary_route(environment_id: str | None = Query(default=None)) -> dict[str, object]:
    """Return deterministic curated intelligence summary for one environment."""
    active_environment_id = environment_id or primary_environment_id()
    payload = intelligence_summary(
        list_inventory(active_environment_id),
        list_assets(active_environment_id),
        list_findings(active_environment_id),
    )
    logger.info("event=intelligence_summary environment_id=%s", active_environment_id)
    return payload


@app.get("/intelligence/advisories")
def intelligence_advisories(environment_id: str | None = Query(default=None)) -> list[object]:
    """Return source-controlled curated advisories."""
    active_environment_id = environment_id or primary_environment_id()
    records = list_advisories()
    logger.info("event=intelligence_advisories environment_id=%s count=%d", active_environment_id, len(records))
    return records


@app.get("/intelligence/trends")
def intelligence_trends(environment_id: str | None = Query(default=None)) -> list[object]:
    """Return source-controlled current risk trends."""
    active_environment_id = environment_id or primary_environment_id()
    records = list_trends()
    logger.info("event=intelligence_trends environment_id=%s count=%d", active_environment_id, len(records))
    return records


@app.get("/intelligence/relevant-findings", response_model=list[Finding])
def intelligence_relevant_findings_route(environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return findings reprioritized with curated intelligence context."""
    active_environment_id = environment_id or primary_environment_id()
    records = intelligence_relevant_findings(
        list_inventory(active_environment_id),
        list_assets(active_environment_id),
        list_findings(active_environment_id),
    )
    logger.info("event=intelligence_relevant_findings environment_id=%s count=%d", active_environment_id, len(records))
    return records


@app.get("/intelligence/update-runs")
def intelligence_update_runs() -> list[object]:
    """Return curated intelligence update run history."""
    records = list_intelligence_update_runs()
    logger.info("event=intelligence_update_runs count=%d", len(records))
    return records


@app.get("/automation/runs", response_model=list[AutomationRun])
def automation_runs(environment_id: str | None = Query(default=None)) -> list[AutomationRun]:
    """Return safe defensive automation run history."""
    records = list_automation_runs(environment_id)
    logger.info("event=list_automation_runs environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/scheduler/status")
def scheduler_status() -> dict[str, object]:
    """Return safe automation scheduler status."""
    status = scheduler.status()
    logger.info("event=scheduler_status mode=%s", status["mode"])
    return status


@app.post("/scheduler/run/tracking", response_model=AutomationRun)
def scheduler_run_tracking(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Run the scheduled tracking job now."""
    run = scheduler.run_now("tracking", lambda: run_tracking_cycle(environment_id))
    logger.info("event=scheduler_run_tracking run_id=%s", run.run_id)
    return run


@app.post("/scheduler/run/intelligence")
def scheduler_run_intelligence(environment_id: str | None = Query(default=None)) -> object:
    """Run the scheduled intelligence update job now."""
    active_environment_id = environment_id or primary_environment_id()
    run = scheduler.run_now(
        "intelligence",
        lambda: run_intelligence_update(
            list_inventory(active_environment_id),
            list_assets(active_environment_id),
            list_findings(active_environment_id),
        ),
    )
    logger.info("event=scheduler_run_intelligence run_id=%s", run.run_id)
    return run


@app.post("/scheduler/run/inventory", response_model=AutomationRun)
def scheduler_run_inventory(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Run the scheduled inventory match job now."""
    run = scheduler.run_now("inventory", lambda: run_inventory_match(environment_id))
    logger.info("event=scheduler_run_inventory run_id=%s", run.run_id)
    return run


@app.post("/automation/discover-assets", response_model=AutomationRun)
def automation_discover_assets(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Safely derive tracked assets from approved posture inventory."""
    run = discover_assets(environment_id)
    logger.info("event=discover_assets run_id=%s assets_discovered=%d", run.run_id, run.assets_discovered)
    return run


@app.post("/automation/derive-findings", response_model=AutomationRun)
def automation_derive_findings(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Safely derive defensive findings from tracked asset metadata."""
    run = derive_findings(environment_id)
    logger.info("event=derive_findings run_id=%s findings_created=%d", run.run_id, run.findings_created)
    return run


@app.post("/automation/refresh-posture", response_model=AutomationRun)
def automation_refresh_posture(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Safely refresh posture summaries from tracked in-memory data."""
    run = refresh_posture(environment_id)
    logger.info("event=refresh_posture run_id=%s posture_score=%d", run.run_id, run.posture_score)
    return run


@app.post("/automation/run-tracking-cycle", response_model=AutomationRun)
def automation_run_tracking_cycle(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Run the safe defensive tracking cycle."""
    run = run_tracking_cycle(environment_id)
    logger.info(
        "event=run_tracking_cycle run_id=%s assets_discovered=%d findings_created=%d posture_score=%d",
        run.run_id,
        run.assets_discovered,
        run.findings_created,
        run.posture_score,
    )
    return run


@app.post("/automation/run-inventory-match", response_model=AutomationRun)
def automation_run_inventory_match(environment_id: str | None = Query(default=None)) -> AutomationRun:
    """Match approved inventory against seeded CVE data."""
    run = run_inventory_match(environment_id)
    logger.info(
        "event=run_inventory_match run_id=%s findings_created=%d posture_score=%d",
        run.run_id,
        run.findings_created,
        run.posture_score,
    )
    return run


@app.post("/automation/update-intelligence")
def automation_update_intelligence(environment_id: str | None = Query(default=None)) -> object:
    """Refresh source-controlled curated intelligence context."""
    active_environment_id = environment_id or primary_environment_id()
    run = run_intelligence_update(
        list_inventory(active_environment_id),
        list_assets(active_environment_id),
        list_findings(active_environment_id),
    )
    logger.info(
        "event=update_intelligence run_id=%s findings_reprioritized=%d status=%s",
        run.run_id,
        run.findings_reprioritized,
        run.status,
    )
    return run
