from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urlparse
from uuid import uuid4

from datasources.models import DataSource, DataSourceCreate, DataSourceTestRequest, DataSourceTestResult
from datasources.pipeline import ingest_datasource
from persistence.database import db
from persistence.store import get_environment, list_environments
from planner.schemas import utc_now


_DATASOURCES: dict[str, DataSource] = {}
_SECRET_FIELDS = {"token", "password", "secret", "api_key", "apikey", "authorization"}
_ALLOWED_FILE_ROOT = Path(__file__).resolve().parents[1] / "data"


def initialize_datasources() -> None:
    if db.enabled:
        for record in db.list_records("datasources", DataSource):
            _DATASOURCES[record.datasource_id] = record

    for environment in list_environments():
        for datasource_type, name in (
            ("inventory", "Approved Inventory"),
            ("scanner_results", "Assessment Results"),
        ):
            datasource_id = f"{environment.environment_id}-{datasource_type}"
            if datasource_id not in _DATASOURCES:
                save_datasource(
                    DataSourceCreate(
                        environment_id=environment.environment_id,
                        name=name,
                        type=datasource_type,
                        status="enabled",
                        config={"managed": True},
                        ingestion_enabled=False,
                        ingestion_interval_seconds=None,
                    ),
                    datasource_id=datasource_id,
                )


def save_datasource(payload: DataSourceCreate, datasource_id: str | None = None) -> DataSource:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")

    existing = _DATASOURCES.get(datasource_id or "")
    now = utc_now()
    record = DataSource(
        datasource_id=datasource_id or f"ds-{uuid4().hex[:12]}",
        environment_id=payload.environment_id,
        name=payload.name,
        type=payload.type,
        status=payload.status,
        config=payload.config,
        created_at=existing.created_at if existing else now,
        updated_at=now,
        last_tested_at=existing.last_tested_at if existing else None,
        ingestion_enabled=payload.ingestion_enabled,
        ingestion_interval_seconds=payload.ingestion_interval_seconds,
    )
    _DATASOURCES[record.datasource_id] = record
    if db.enabled:
        db.upsert_many("datasources", [record])
    return record


def list_datasources(environment_id: str | None = None) -> list[DataSource]:
    if environment_id:
        return list_datasources_by_environment(environment_id)
    return sorted(_DATASOURCES.values(), key=lambda item: (item.environment_id, item.name.lower()))


def get_datasource(datasource_id: str) -> DataSource | None:
    return _DATASOURCES.get(datasource_id)


def list_datasources_by_environment(environment_id: str) -> list[DataSource]:
    return sorted(
        [item for item in _DATASOURCES.values() if item.environment_id == environment_id],
        key=lambda item: item.name.lower(),
    )


def test_datasource_connection(payload: DataSourceTestRequest) -> DataSourceTestResult:
    if get_environment(payload.environment_id) is None:
        raise ValueError("Environment not found")

    config = _sanitize_config(payload.config)
    tester = {
        "prometheus": _test_http_source,
        "loki": _test_http_source,
        "api": _test_http_source,
        "file": _test_file_source,
        "inventory": _test_internal_source,
        "scanner_results": _test_internal_source,
    }[payload.type]
    return tester(payload.environment_id, config)


def mark_datasource_tested(datasource_id: str, result: DataSourceTestResult) -> DataSource | None:
    existing = _DATASOURCES.get(datasource_id)
    if existing is None:
        return None
    updated = existing.model_copy(update={"last_tested_at": result.checked_at, "status": result.status, "updated_at": utc_now()})
    _DATASOURCES[datasource_id] = updated
    if db.enabled:
        db.upsert_many("datasources", [updated])
    return updated


def update_datasource_ingestion(datasource_id: str, enabled: bool, interval_seconds: int | None) -> DataSource | None:
    existing = _DATASOURCES.get(datasource_id)
    if existing is None:
        return None
    updated = existing.model_copy(
        update={
            "ingestion_enabled": enabled,
            "ingestion_interval_seconds": interval_seconds if enabled else None,
            "updated_at": utc_now(),
        }
    )
    _DATASOURCES[datasource_id] = updated
    if db.enabled:
        db.upsert_many("datasources", [updated])
    return updated


def ingest_environment_datasources(environment_id: str) -> dict[str, int]:
    ingested: dict[str, int] = {}
    for datasource in list_datasources_by_environment(environment_id):
        if datasource.status != "enabled":
            continue
        try:
            ingested[datasource.datasource_id] = len(ingest_datasource(datasource))
        except Exception:  # noqa: BLE001
            ingested[datasource.datasource_id] = 0
    return ingested


def _test_internal_source(environment_id: str, config: dict[str, Any]) -> DataSourceTestResult:
    return DataSourceTestResult(
        ok=True,
        status="enabled",
        message=f"Environment-scoped {config.get('managed_label', 'internal')} source is ready for {environment_id}.",
    )


def _test_file_source(environment_id: str, config: dict[str, Any]) -> DataSourceTestResult:
    raw_path = str(config.get("path", "")).strip()
    if not raw_path:
        return DataSourceTestResult(ok=False, status="error", message="config.path is required for file data sources")

    candidate = Path(raw_path)
    resolved = candidate if candidate.is_absolute() else (_ALLOWED_FILE_ROOT / candidate)
    resolved = resolved.resolve()
    if _ALLOWED_FILE_ROOT not in resolved.parents and resolved != _ALLOWED_FILE_ROOT:
        return DataSourceTestResult(ok=False, status="error", message="File data sources must stay within backend/data")
    if not resolved.exists():
        return DataSourceTestResult(ok=False, status="error", message="Configured file path does not exist")
    return DataSourceTestResult(ok=True, status="enabled", message=f"File source validated for {environment_id}")


def _test_http_source(environment_id: str, config: dict[str, Any]) -> DataSourceTestResult:
    url = str(config.get("url", "")).strip()
    if not url:
        return DataSourceTestResult(ok=False, status="error", message="config.url is required for HTTP-backed data sources")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return DataSourceTestResult(ok=False, status="error", message="config.url must be a valid http or https URL")

    timeout = min(max(int(config.get("timeout_seconds", 2)), 1), 5)
    request_headers = {"User-Agent": "PurpleClaw/0.1 datasource-test"}
    try:
        probe = request.Request(url, method="GET", headers=request_headers)
        with request.urlopen(probe, timeout=timeout) as response:  # noqa: S310
            status_code = getattr(response, "status", 200)
        if 200 <= status_code < 500:
            return DataSourceTestResult(ok=True, status="enabled", message=f"HTTP source responded for {environment_id}")
        return DataSourceTestResult(ok=False, status="error", message=f"HTTP source returned status {status_code}")
    except error.HTTPError as exc:
        if 200 <= exc.code < 500:
            return DataSourceTestResult(ok=True, status="enabled", message=f"HTTP source responded with status {exc.code}")
        return DataSourceTestResult(ok=False, status="error", message=f"HTTP source returned status {exc.code}")
    except Exception as exc:  # noqa: BLE001
        return DataSourceTestResult(ok=False, status="error", message=f"HTTP source validation failed: {exc.__class__.__name__}")


def _sanitize_config(config: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in config.items():
        if key.lower() in _SECRET_FIELDS:
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    return sanitized
