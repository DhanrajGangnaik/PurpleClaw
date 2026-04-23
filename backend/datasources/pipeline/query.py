from __future__ import annotations

from collections import defaultdict
from typing import Any

from datasources.pipeline.models import DataRecord, QuerySpec
from datasources.pipeline.storage import list_records


def query_data(environment_id: str, query_spec: QuerySpec | dict[str, Any]) -> dict[str, Any]:
    spec = query_spec if isinstance(query_spec, QuerySpec) else QuerySpec.model_validate(query_spec)
    records = list_records(environment_id)
    filtered: list[DataRecord] = []
    for record in records:
        if spec.record_types and record.record_type not in spec.record_types:
            continue
        if spec.metrics and record.metric not in spec.metrics:
            continue
        if spec.tags and not any(tag in record.tags for tag in spec.tags):
            continue
        if spec.start_at and record.observed_at < spec.start_at:
            continue
        if spec.end_at and record.observed_at > spec.end_at:
            continue
        filtered.append(record)

    if spec.aggregate == "raw":
        return {"records": [record.model_dump(mode="json") for record in filtered[: spec.limit]], "count": len(filtered)}

    grouped: dict[str, list[float]] = defaultdict(list)
    for record in filtered:
        key_parts = [str(record.dimensions.get(field, "all")) for field in spec.group_by] or [record.metric]
        if isinstance(record.value, bool):
            grouped["|".join(key_parts)].append(float(int(record.value)))
        elif isinstance(record.value, int | float):
            grouped["|".join(key_parts)].append(float(record.value))

    aggregates = []
    for key, values in grouped.items():
        if spec.aggregate == "count":
            value = len(values)
        elif spec.aggregate == "avg":
            value = round(sum(values) / len(values), 2) if values else 0
        elif spec.aggregate == "sum":
            value = round(sum(values), 2)
        else:
            value = len(values)
        aggregates.append({"group": key, "value": value})
    return {"aggregates": aggregates[: spec.limit], "count": len(filtered)}
