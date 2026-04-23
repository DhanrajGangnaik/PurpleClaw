from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from datasources.jobs.models import DatasourceIngestionJob
from persistence.database import db
from planner.schemas import utc_now


_INGESTION_JOBS: dict[str, DatasourceIngestionJob] = {}


def initialize_ingestion_jobs() -> None:
    if db.enabled:
        for record in db.list_records("datasource_ingestion_jobs", DatasourceIngestionJob):
            _INGESTION_JOBS[record.job_id] = record


def save_job(job: DatasourceIngestionJob) -> DatasourceIngestionJob:
    _INGESTION_JOBS[job.job_id] = job
    if db.enabled:
        db.upsert_many("datasource_ingestion_jobs", [job])
    return job


def create_or_update_job(
    datasource_id: str,
    environment_id: str,
    trigger_mode: str,
    interval_seconds: int | None,
    enabled: bool,
) -> DatasourceIngestionJob:
    existing = next((job for job in _INGESTION_JOBS.values() if job.datasource_id == datasource_id), None)
    now = utc_now()
    next_run_at = None
    if enabled and trigger_mode == "interval" and interval_seconds:
        next_run_at = now + timedelta(seconds=interval_seconds)
    job = DatasourceIngestionJob(
        job_id=existing.job_id if existing else f"ingest-{uuid4().hex[:12]}",
        datasource_id=datasource_id,
        environment_id=environment_id,
        status="scheduled" if enabled else "disabled",
        trigger_mode=trigger_mode,  # type: ignore[arg-type]
        interval_seconds=interval_seconds,
        last_run_at=existing.last_run_at if existing else None,
        next_run_at=next_run_at if enabled else None,
        last_status_message=existing.last_status_message if existing else None,
        records_ingested=existing.records_ingested if existing else 0,
        created_at=existing.created_at if existing else now,
        updated_at=now,
    )
    return save_job(job)


def list_jobs(environment_id: str | None = None) -> list[DatasourceIngestionJob]:
    records = _INGESTION_JOBS.values()
    if environment_id:
        records = [job for job in records if job.environment_id == environment_id]
    return sorted(records, key=lambda item: item.updated_at, reverse=True)


def get_job(job_id: str) -> DatasourceIngestionJob | None:
    return _INGESTION_JOBS.get(job_id)


def get_job_by_datasource(datasource_id: str) -> DatasourceIngestionJob | None:
    return next((job for job in _INGESTION_JOBS.values() if job.datasource_id == datasource_id), None)


def mark_job_running(job: DatasourceIngestionJob) -> DatasourceIngestionJob:
    updated = job.model_copy(update={"status": "running", "updated_at": utc_now(), "last_status_message": "Ingestion is running."})
    return save_job(updated)


def mark_job_completed(job: DatasourceIngestionJob, records_ingested: int, message: str) -> DatasourceIngestionJob:
    now = utc_now()
    next_run_at = None
    if job.status != "disabled" and job.trigger_mode == "interval" and job.interval_seconds:
        next_run_at = now + timedelta(seconds=job.interval_seconds)
    updated = job.model_copy(
        update={
            "status": "completed" if job.status != "disabled" else "disabled",
            "last_run_at": now,
            "next_run_at": next_run_at,
            "records_ingested": job.records_ingested + records_ingested,
            "last_status_message": message,
            "updated_at": now,
        }
    )
    return save_job(updated)


def mark_job_failed(job: DatasourceIngestionJob, message: str) -> DatasourceIngestionJob:
    now = utc_now()
    next_run_at = None
    if job.trigger_mode == "interval" and job.interval_seconds and job.status != "disabled":
        next_run_at = now + timedelta(seconds=job.interval_seconds)
    updated = job.model_copy(
        update={
            "status": "failed",
            "last_run_at": now,
            "next_run_at": next_run_at,
            "last_status_message": message,
            "updated_at": now,
        }
    )
    return save_job(updated)


def disable_job(job: DatasourceIngestionJob) -> DatasourceIngestionJob:
    updated = job.model_copy(update={"status": "disabled", "next_run_at": None, "updated_at": utc_now(), "last_status_message": "Ingestion disabled."})
    return save_job(updated)
