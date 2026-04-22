import logging
from typing import Union

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from collectors.loki import get_loki_config, get_loki_health
from collectors.prometheus import get_prometheus_config, get_prometheus_health
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
    list_reports,
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
    Report,
    RemediationTask,
    RiskByAsset,
    SecuritySignal,
    ServiceHealth,
    SystemMode,
    TelemetrySourceHealth,
)
from scheduler import scheduler
from persistence.database import db


class RestoreRequest(BaseModel):
    filename: str

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


@app.get("/environments/{environment_id}", response_model=Environment)
def environment(environment_id: str) -> Environment:
    """Return one configured PurpleClaw environment."""
    record = get_environment(environment_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Environment not found")
    logger.info("event=get_environment environment_id=%s", environment_id)
    return record


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


@app.get("/reports", response_model=list[Report])
def reports() -> list[Report]:
    """Return generated posture reports."""
    records = list_reports()
    logger.info("event=list_reports count=%d", len(records))
    return records


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
