from __future__ import annotations

from datasources.jobs import (
    DatasourceIngestionJob,
    create_or_update_job,
    disable_job,
    get_job_by_datasource,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
)
from datasources.pipeline import ingest_datasource
from datasources.store import get_datasource, update_datasource_ingestion
from scheduler import scheduler


_APPROVED_INGESTION_TYPES = {"prometheus", "loki", "api", "file", "inventory", "scanner_results"}


def schedule_datasource_ingestion(datasource_id: str, trigger_mode: str, interval_seconds: int | None, enabled: bool) -> DatasourceIngestionJob:
    datasource = get_datasource(datasource_id)
    if datasource is None:
        raise ValueError("Data source not found")
    if datasource.type not in _APPROVED_INGESTION_TYPES:
        raise ValueError("Datasource type is not approved for ingestion")

    updated = update_datasource_ingestion(datasource_id, enabled, interval_seconds)
    if updated is None:
        raise ValueError("Data source not found")
    job = create_or_update_job(updated.datasource_id, updated.environment_id, trigger_mode, interval_seconds, enabled)
    scheduler.remove_interval_job(f"datasource:{datasource_id}")
    if enabled and trigger_mode == "interval" and interval_seconds:
        scheduler.register_interval_job(f"datasource:{datasource_id}", interval_seconds, lambda: run_ingestion_job(datasource_id))
    return job


def disable_datasource_ingestion(datasource_id: str) -> DatasourceIngestionJob:
    datasource = get_datasource(datasource_id)
    if datasource is None:
        raise ValueError("Data source not found")
    update_datasource_ingestion(datasource_id, False, None)
    job = get_job_by_datasource(datasource_id)
    if job is None:
        job = create_or_update_job(datasource.datasource_id, datasource.environment_id, "manual", None, False)
    scheduler.remove_interval_job(f"datasource:{datasource_id}")
    return disable_job(job)


def run_ingestion_job(datasource_id: str) -> DatasourceIngestionJob:
    datasource = get_datasource(datasource_id)
    if datasource is None:
        raise ValueError("Data source not found")
    if datasource.status != "enabled" or not datasource.ingestion_enabled:
        job = get_job_by_datasource(datasource_id) or create_or_update_job(datasource.datasource_id, datasource.environment_id, "manual", None, False)
        return disable_job(job)
    if datasource.type not in _APPROVED_INGESTION_TYPES:
        raise ValueError("Datasource type is not approved for ingestion")

    job = get_job_by_datasource(datasource_id) or create_or_update_job(
        datasource.datasource_id,
        datasource.environment_id,
        "manual",
        datasource.ingestion_interval_seconds,
        datasource.ingestion_enabled,
    )
    mark_job_running(job)
    try:
        records = ingest_datasource(datasource)
        message = f"Ingested {len(records)} record(s) from approved datasource."
        return mark_job_completed(get_job_by_datasource(datasource_id) or job, len(records), message)
    except Exception as exc:  # noqa: BLE001
        sanitized = f"{exc.__class__.__name__}: ingestion failed safely"
        return mark_job_failed(get_job_by_datasource(datasource_id) or job, sanitized)
