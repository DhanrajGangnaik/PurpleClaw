import logging
from typing import Union

from fastapi import FastAPI, HTTPException, Query

from collectors.prometheus import get_prometheus_config, get_prometheus_health
from executor import get_executor
from executor.models import ExecutionResult
from persistence import (
    derive_findings,
    discover_assets,
    findings_count_by_severity,
    get_environment,
    get_prometheus_metrics,
    get_system_mode,
    list_automation_runs,
    list_assets,
    list_environments,
    list_execution_results,
    list_findings,
    list_findings_for_asset,
    list_plans,
    list_policies,
    list_remediations,
    list_remediations_for_finding,
    list_reports,
    list_telemetry_summaries,
    primary_environment_id,
    remediation_completion_percentage,
    refresh_posture,
    risk_by_asset,
    run_tracking_cycle,
    save_execution_result,
    save_plan,
)
from planner import ValidationResult, validate_exercise_plan
from planner.schemas import ExercisePlan
from posture.models import Asset, AutomationRun, Environment, Finding, Policy, Report, RemediationTask, SystemMode

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PurpleClaw",
    description="Open-source AI-assisted purple-team validation platform.",
    version="0.1.0",
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


@app.get("/findings", response_model=list[Finding])
def findings(environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return defensive posture findings."""
    records = list_findings(environment_id)
    logger.info("event=list_findings environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


@app.get("/findings/{asset_id}", response_model=list[Finding])
def findings_for_asset(asset_id: str, environment_id: str | None = Query(default=None)) -> list[Finding]:
    """Return defensive posture findings for one asset."""
    records = list_findings_for_asset(asset_id, environment_id)
    logger.info("event=list_findings_for_asset asset_id=%s environment_id=%s count=%d", asset_id, environment_id or primary_environment_id(), len(records))
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
    }
    logger.info("event=telemetry_summary environment_id=%s summaries=%d", environment_id or primary_environment_id(), len(summaries))
    return payload


@app.get("/automation/runs", response_model=list[AutomationRun])
def automation_runs(environment_id: str | None = Query(default=None)) -> list[AutomationRun]:
    """Return safe defensive automation run history."""
    records = list_automation_runs(environment_id)
    logger.info("event=list_automation_runs environment_id=%s count=%d", environment_id or primary_environment_id(), len(records))
    return records


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
