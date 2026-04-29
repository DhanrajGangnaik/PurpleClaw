from __future__ import annotations

import json
import os
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


def _build_configs() -> dict[str, LokiSourceConfig]:
    """Build configs from environment variables at startup."""
    configs: dict[str, LokiSourceConfig] = {}
    timeout = float(os.getenv("LOKI_TIMEOUT", "3.0"))

    # Primary: LOKI_URL (environment id from LOKI_ENV_ID, default "default")
    primary_url = os.getenv("LOKI_URL", "").strip()
    if primary_url:
        env_id = os.getenv("LOKI_ENV_ID", "default")
        configs[env_id] = LokiSourceConfig(
            environment_id=env_id,
            base_url=primary_url.rstrip("/"),
            enabled=True,
            timeout_seconds=timeout,
        )

    # Additional environments: LOKI_URL_<ENV_ID>=url
    # e.g. LOKI_URL_STAGING=http://staging-loki:3100
    for key, val in os.environ.items():
        if key.startswith("LOKI_URL_") and val.strip():
            env_id = key[len("LOKI_URL_"):].lower()
            if env_id:
                configs[env_id] = LokiSourceConfig(
                    environment_id=env_id,
                    base_url=val.strip().rstrip("/"),
                    enabled=True,
                    timeout_seconds=timeout,
                )

    return configs


LOKI_CONFIGS: dict[str, LokiSourceConfig] = _build_configs()
PRIMARY_ENVIRONMENT_ID = os.getenv("LOKI_ENV_ID", next(iter(LOKI_CONFIGS), "default"))
QUERY_LIMIT = os.getenv("LOKI_QUERY_LIMIT", "250")
SIX_HOURS_SECONDS = 6 * 60 * 60
RECENT_SECONDS = 15 * 60

# Expected log sources per environment (configurable via LOKI_EXPECTED_SOURCES_<ENV>=src1,src2)
def _expected_sources(env_id: str) -> list[str]:
    env_key = f"LOKI_EXPECTED_SOURCES_{env_id.upper()}"
    raw = os.getenv(env_key, os.getenv("LOKI_EXPECTED_SOURCES", "")).strip()
    if raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return []


_NOT_CONFIGURED = {
    "environment_id": "default",
    "enabled": False,
    "status": "not-configured",
    "healthy": False,
    "message": "Loki URL not configured. Set LOKI_URL environment variable.",
}


def get_loki_config(environment_id: str | None = None) -> dict[str, object]:
    """Return read-only Loki configuration for an environment."""
    config = _config_for(environment_id)
    if config is None:
        return {**_NOT_CONFIGURED, "base_url": "", "timeout_seconds": 3.0}
    return asdict(config)


def get_loki_health(environment_id: str | None = None) -> dict[str, object]:
    """Check whether the configured Loki API is reachable."""
    config = _config_for(environment_id)
    if config is None:
        return _NOT_CONFIGURED.copy()

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
    """Return log source coverage using Loki API queries."""
    config = _config_for(environment_id)
    if config is None:
        return _empty_log_source_summary("default", "not-configured", [])

    expected_sources = _expected_sources(config.environment_id)
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
    missing_sources = [src for src in expected_sources if not _source_present(src, active_sources)]
    stale_sources = [src for src in active_sources if src not in recent_source_names]
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
    """Return authentication failure signals from Loki queries."""
    config = _config_for(environment_id)
    if config is None:
        return _empty_signal_summary("default", "not-configured")

    if not config.enabled:
        return _empty_signal_summary(config.environment_id, "disabled")

    response = _query_logs(
        config,
        '{job=~".+"} |~ "(?i)(authentication failed|auth failure|failed password|invalid login|login failed)"',
        SIX_HOURS_SECONDS,
    )
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
    """Return service error signals from Loki queries."""
    config = _config_for(environment_id)
    if config is None:
        return _empty_signal_summary("default", "not-configured")

    if not config.enabled:
        return _empty_signal_summary(config.environment_id, "disabled")

    response = _query_logs(
        config,
        '{job=~".+"} |~ "(?i)(error|exception|panic|5[0-9]{2})"',
        SIX_HOURS_SECONDS,
    )
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


def get_all_environments() -> list[str]:
    """Return all configured environment IDs."""
    return list(LOKI_CONFIGS.keys())


def _config_for(environment_id: str | None) -> LokiSourceConfig | None:
    if not LOKI_CONFIGS:
        return None
    if environment_id and environment_id in LOKI_CONFIGS:
        return LOKI_CONFIGS[str(environment_id)]
    if PRIMARY_ENVIRONMENT_ID in LOKI_CONFIGS:
        return LOKI_CONFIGS[PRIMARY_ENVIRONMENT_ID]
    return next(iter(LOKI_CONFIGS.values()))


def _request_json(config: LokiSourceConfig, path: str, params: dict[str, str]) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{config.base_url.rstrip('/')}{path}{query}"
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc), "data": {}}

    return {
        "ok": payload.get("status") == "success",
        "error": "" if payload.get("status") == "success" else str(payload),
        "data": payload,
    }


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
        "missing_sources": expected_sources if status not in ("disabled", "not-configured") else [],
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
