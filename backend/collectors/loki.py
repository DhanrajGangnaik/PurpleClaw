from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LokiSourceConfig:
    """Read-only Loki source settings for one environment."""

    environment_id: str
    base_url: str
    enabled: bool
    timeout_seconds: float


LOKI_CONFIGS: dict[str, LokiSourceConfig] = {
    "homelab": LokiSourceConfig(
        environment_id="homelab",
        base_url="http://127.0.0.1:3100",
        enabled=True,
        timeout_seconds=1.5,
    ),
    "lab": LokiSourceConfig(
        environment_id="lab",
        base_url="http://127.0.0.1:3101",
        enabled=True,
        timeout_seconds=1.5,
    ),
    "staging": LokiSourceConfig(
        environment_id="staging",
        base_url="http://127.0.0.1:3102",
        enabled=False,
        timeout_seconds=1.5,
    ),
}
PRIMARY_ENVIRONMENT_ID = "homelab"
QUERY_LIMIT = "250"
SIX_HOURS_SECONDS = 6 * 60 * 60
RECENT_SECONDS = 15 * 60
EXPECTED_LOG_SOURCES: dict[str, list[str]] = {
    "homelab": ["auth", "audit", "syslog"],
    "lab": ["audit", "kubernetes", "container-runtime"],
    "staging": ["application", "auth", "container-runtime"],
}


def get_loki_config(environment_id: str | None = None) -> dict[str, object]:
    """Return read-only Loki configuration for an environment."""

    return asdict(_config_for(environment_id))


def get_loki_health(environment_id: str | None = None) -> dict[str, object]:
    """Check whether the configured Loki API is reachable."""

    config = _config_for(environment_id)
    if not config.enabled:
        return {
            "environment_id": config.environment_id,
            "enabled": False,
            "status": "disabled",
            "healthy": False,
            "message": "Loki integration is disabled for this environment.",
        }

    response = _request_json(config, "/loki/api/v1/labels", {})
    return {
        "environment_id": config.environment_id,
        "enabled": True,
        "status": "healthy" if response["ok"] else "unavailable",
        "healthy": response["ok"],
        "message": response["error"] or "Loki API is reachable.",
    }


def get_log_source_summary(environment_id: str | None = None) -> dict[str, object]:
    """Return log source coverage using fixed read-only Loki API queries."""

    config = _config_for(environment_id)
    expected_sources = EXPECTED_LOG_SOURCES.get(config.environment_id, [])
    if not config.enabled:
        return _empty_log_source_summary(config.environment_id, "disabled", expected_sources)

    historical_response = _query_logs(config, '{job=~".+"}', SIX_HOURS_SECONDS)
    if not historical_response["ok"]:
        summary = _empty_log_source_summary(config.environment_id, "unavailable", expected_sources)
        summary["message"] = historical_response["error"]
        return summary

    recent_response = _query_logs(config, '{job=~".+"}', RECENT_SECONDS)
    historical_sources = _source_counts(historical_response["data"])
    recent_sources = _source_counts(recent_response["data"] if recent_response["ok"] else {})
    active_sources = sorted(historical_sources)
    recent_source_names = set(recent_sources)
    missing_sources = [source for source in expected_sources if not _source_present(source, active_sources)]
    stale_sources = [source for source in active_sources if source not in recent_source_names]
    event_count = sum(historical_sources.values())
    newest_log_at = _newest_log_at(historical_response["data"])

    if missing_sources:
        status = "coverage-gap"
    elif stale_sources:
        status = "stale"
    elif event_count > 0:
        status = "healthy"
    else:
        status = "empty"

    return {
        "environment_id": config.environment_id,
        "status": status,
        "source_count": len(active_sources),
        "active_sources": active_sources,
        "expected_sources": expected_sources,
        "missing_sources": missing_sources,
        "stale_sources": stale_sources,
        "event_count": event_count,
        "newest_log_at": newest_log_at,
        "message": "Loki log source coverage loaded.",
    }


def get_auth_failure_summary(environment_id: str | None = None) -> dict[str, object]:
    """Return authentication failure signals from fixed Loki queries."""

    config = _config_for(environment_id)
    if not config.enabled:
        return _empty_signal_summary(config.environment_id, "disabled")

    response = _query_logs(config, '{job=~".+"} |~ "(?i)(authentication failed|auth failure|failed password|invalid login|login failed)"', SIX_HOURS_SECONDS)
    if not response["ok"]:
        summary = _empty_signal_summary(config.environment_id, "unavailable")
        summary["message"] = response["error"]
        return summary

    sources = _source_counts(response["data"])
    event_count = sum(sources.values())
    return {
        "environment_id": config.environment_id,
        "status": "elevated" if event_count >= 5 else "observed" if event_count > 0 else "quiet",
        "event_count": event_count,
        "source_count": len(sources),
        "sources": sorted(sources),
        "message": "Authentication signals loaded from Loki.",
    }


def get_service_error_summary(environment_id: str | None = None) -> dict[str, object]:
    """Return service error signals from fixed Loki queries."""

    config = _config_for(environment_id)
    if not config.enabled:
        return _empty_signal_summary(config.environment_id, "disabled")

    response = _query_logs(config, '{job=~".+"} |~ "(?i)(error|exception|panic|5[0-9]{2})"', SIX_HOURS_SECONDS)
    if not response["ok"]:
        summary = _empty_signal_summary(config.environment_id, "unavailable")
        summary["message"] = response["error"]
        return summary

    sources = _source_counts(response["data"])
    event_count = sum(sources.values())
    return {
        "environment_id": config.environment_id,
        "status": "elevated" if event_count >= 10 else "observed" if event_count > 0 else "quiet",
        "event_count": event_count,
        "source_count": len(sources),
        "sources": sorted(sources),
        "message": "Service error signals loaded from Loki.",
    }


def get_environment_log_metrics(environment_id: str | None = None) -> dict[str, object]:
    """Return a safe read-only Loki rollup for one environment."""

    config = get_loki_config(environment_id)
    health = get_loki_health(environment_id)
    log_source_summary = get_log_source_summary(environment_id)
    auth_failure_summary = get_auth_failure_summary(environment_id)
    service_error_summary = get_service_error_summary(environment_id)
    return {
        "environment_id": config["environment_id"],
        "config": config,
        "health": health,
        "log_source_summary": log_source_summary,
        "auth_failure_summary": auth_failure_summary,
        "service_error_summary": service_error_summary,
    }


def _config_for(environment_id: str | None) -> LokiSourceConfig:
    if environment_id in LOKI_CONFIGS:
        return LOKI_CONFIGS[str(environment_id)]
    return LOKI_CONFIGS[PRIMARY_ENVIRONMENT_ID]


def _request_json(config: LokiSourceConfig, path: str, params: dict[str, str]) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{config.base_url.rstrip('/')}{path}{query}"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "data": {}}

    return {"ok": payload.get("status") == "success", "error": "" if payload.get("status") == "success" else str(payload), "data": payload}


def _query_logs(config: LokiSourceConfig, query: str, seconds: int) -> dict[str, Any]:
    end = time.time_ns()
    start = end - (seconds * 1_000_000_000)
    return _request_json(
        config,
        "/loki/api/v1/query_range",
        {
            "query": query,
            "start": str(start),
            "end": str(end),
            "limit": QUERY_LIMIT,
            "direction": "backward",
        },
    )


def _source_counts(payload: dict[str, Any]) -> dict[str, int]:
    streams = payload.get("data", {}).get("result", [])
    if not isinstance(streams, list):
        return {}

    counts: dict[str, int] = {}
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        metric = stream.get("stream", {})
        if not isinstance(metric, dict):
            metric = {}
        source = _source_label(metric)
        values = stream.get("values", [])
        counts[source] = counts.get(source, 0) + (len(values) if isinstance(values, list) else 0)
    return counts


def _source_label(labels: dict[str, object]) -> str:
    for key in ("source", "job", "app", "service", "container", "filename"):
        value = labels.get(key)
        if value:
            return str(value)
    return "unknown"


def _source_present(expected_source: str, observed_sources: list[str]) -> bool:
    expected = expected_source.lower()
    return any(expected in source.lower() for source in observed_sources)


def _newest_log_at(payload: dict[str, Any]) -> str | None:
    newest: int | None = None
    streams = payload.get("data", {}).get("result", [])
    if not isinstance(streams, list):
        return None
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        values = stream.get("values", [])
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, list) or not value:
                continue
            try:
                timestamp = int(value[0])
            except (TypeError, ValueError):
                continue
            newest = max(newest or timestamp, timestamp)
    if newest is None:
        return None
    return datetime.fromtimestamp(newest / 1_000_000_000, tz=timezone.utc).isoformat()


def _empty_log_source_summary(environment_id: str, status: str, expected_sources: list[str]) -> dict[str, object]:
    return {
        "environment_id": environment_id,
        "status": status,
        "source_count": 0,
        "active_sources": [],
        "expected_sources": expected_sources,
        "missing_sources": expected_sources if status != "disabled" else [],
        "stale_sources": [],
        "event_count": 0,
        "newest_log_at": None,
        "message": "No Loki log source data available.",
    }


def _empty_signal_summary(environment_id: str, status: str) -> dict[str, object]:
    return {
        "environment_id": environment_id,
        "status": status,
        "event_count": 0,
        "source_count": 0,
        "sources": [],
        "message": "No Loki signal data available.",
    }
