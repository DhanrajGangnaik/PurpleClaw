from __future__ import annotations

from datasources.jobs import initialize_ingestion_jobs, list_jobs
from datasources.jobs.runtime import schedule_datasource_ingestion


def initialize_ingestion_runtime() -> None:
    initialize_ingestion_jobs()
    for job in list_jobs():
        if job.status != "disabled" and job.trigger_mode == "interval" and job.interval_seconds:
            schedule_datasource_ingestion(job.datasource_id, job.trigger_mode, job.interval_seconds, True)
