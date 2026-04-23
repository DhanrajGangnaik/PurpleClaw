from __future__ import annotations

from datasources.pipeline.models import DataRecord
from persistence.database import db


_DATA_RECORDS: dict[str, DataRecord] = {}


def initialize_storage() -> None:
    if db.enabled:
        for record in db.list_records("data_records", DataRecord):
            _DATA_RECORDS[record.record_id] = record


def save_records(records: list[DataRecord]) -> list[DataRecord]:
    for record in records:
        _DATA_RECORDS[record.record_id] = record
    if db.enabled and records:
        db.upsert_many("data_records", records)
    return records


def list_records(environment_id: str | None = None, datasource_id: str | None = None) -> list[DataRecord]:
    records = _DATA_RECORDS.values()
    if environment_id:
        records = [record for record in records if record.environment_id == environment_id]
    if datasource_id:
        records = [record for record in records if record.datasource_id == datasource_id]
    return sorted(records, key=lambda item: item.observed_at, reverse=True)


def list_records_paginated(
    environment_id: str,
    datasource_id: str,
    record_type: str | None = None,
    start_at=None,
    end_at=None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, object]:
    records = list_records(environment_id, datasource_id)
    if record_type:
        records = [record for record in records if record.record_type == record_type]
    if start_at:
        records = [record for record in records if record.observed_at >= start_at]
    if end_at:
        records = [record for record in records if record.observed_at <= end_at]
    total = len(records)
    start_index = max(page - 1, 0) * page_size
    end_index = start_index + page_size
    return {
        "items": [record.model_dump(mode="json") for record in records[start_index:end_index]],
        "page": page,
        "page_size": page_size,
        "total": total,
    }
