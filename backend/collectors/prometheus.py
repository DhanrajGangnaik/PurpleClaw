from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PrometheusSourceConfig:
    """Read-only Prometheus source settings for one environment."""

    environment_id: str
    base_url: str
    enabled: bool
    timeout_seconds: float


def _build_configs() -> dict[str, PrometheusSourceConfig]:
    """Build configs from environment variables at startup."""
    configs: dict[str, PrometheusSourceConfig] = {}
    timeout = float(os.getenv("PROMETHEUS_TIMEOUT", "3.0"))

    # Primary: PROMETHEUS_URL (environment id from PROMETHEUS_ENV_ID, default "default")
    primary_url = os.getenv("PROMETHEUS_URL", "").strip()
    if primary_url:
        env_id = os.getenv("PROMETHEUS_ENV_ID", "default")
        configs[env_id] = PrometheusSourceConfig(
            environment_id=env_id,
            base_url=primary_url.rstrip("/"),
            enabled=True,
            timeout_seconds=timeout,
        )

    # Additional environments: PROMETHEUS_URL_<ENV_ID>=url
    # e.g. PROMETHEUS_URL_STAGING=http://staging-prom:9090
    for key, val in os.environ.items():
        if key.startswith("PROMETHEUS_URL_") and val.strip():
            env_id = key[len("PROMETHEUS_URL_"):].lower()
            if env_id:
                configs[env_id] = PrometheusSourceConfig(
                    environment_id=env_id,
                    base_url=val.strip().rstrip("/"),
                    enabled=True,
                    timeout_seconds=timeout,
                )

    return configs


PROMETHEUS_CONFIGS: dict[str, PrometheusSourceConfig] = _build_configs()
PRIMARY_ENVIRONMENT_ID = os.getenv("PROMETHEUS_ENV_ID", next(iter(PROMETHEUS_CONFIGS), "default"))

_NOT_CONFIGURED = {
    "environment_id": "default",
    "enabled": False,
    "status": "not-configured",
    "healthy": False,
    "message": "Prometheus URL not configured. Set PROMETHEUS_URL environment variable.",
}


def get_prometheus_config(environment_id: str | None = None) -> dict[str, object]:
    """Return read-only Prometheus configuration for an environment."""
    config = _config_for(environment_id)
    if config is None:
        return {**_NOT_CONFIGURED, "base_url": "", "timeout_seconds": 3.0}
    return asdict(config)


def get_prometheus_health(environment_id: str | None = None) -> dict[str, object]:
    """Check whether the configured Prometheus API is reachable."""
    config = _config_for(environment_id)
    if config is None:
        return _NOT_CONFIGURED.copy()

    if not config.enabled:
        return {
            "environment_id": config.environment_id,
            "enabled": False,
            "status": "disabled",
            "healthy": False,
            "message": "Prometheus integration is disabled for this environment.",
        }

    response = _request_json(config, "/api/v1/query", {"query": "up"})
    return {
        "environment_id": config.environment_id,
        "enabled": True,
        "status": "healthy" if response["ok"] else "unavailable",
        "healthy": response["ok"],
        "message": response["error"] or "Prometheus API is reachable.",
    }


def get_target_summary(environment_id: str | None = None) -> dict[str, object]:
    """Return active scrape target counts and node exporter coverage."""
    config = _config_for(environment_id)
    if config is None:
        return _empty_target_summary("default", "not-configured")

    if not config.enabled:
        return _empty_target_summary(config.environment_id, "disabled")

    response = _request_json(config, "/api/v1/targets", {"state": "active"})
    if not response["ok"]:
        summary = _empty_target_summary(config.environment_id, "unavailable")
        summary["message"] = response["error"]
        return summary

    targets = response["data"].get("data", {}).get("activeTargets", [])
    active_targets = targets if isinstance(targets, list) else []
    up_targets = [t for t in active_targets if t.get("health") == "up"]
    down_targets = [t for t in active_targets if t.get("health") != "up"]
    node_targets = [t for t in active_targets if _is_node_exporter_target(t)]
    node_targets_up = [t for t in node_targets if t.get("health") == "up"]

    return {
        "environment_id": config.environment_id,
        "status": "healthy" if active_targets and not down_targets else "needs-attention" if active_targets else "empty",
        "active_target_count": len(active_targets),
        "up_target_count": len(up_targets),
        "down_target_count": len(down_targets),
        "node_exporter_present": bool(node_targets),
        "node_exporter_up_count": len(node_targets_up),
        "down_targets": [_target_label(t) for t in down_targets[:10]],
        "message": "Prometheus scrape targets loaded.",
    }


def get_node_summary(environment_id: str | None = None) -> dict[str, object]:
    """Return basic node exporter host metric rollups when available."""
    config = _config_for(environment_id)
    target_summary = get_target_summary(environment_id)

    if config is None:
        return _empty_node_summary("default", "not-configured", target_summary)
    if not config.enabled:
        return _empty_node_summary(config.environment_id, "disabled", target_summary)
    if target_summary.get("status") in ("unavailable", "not-configured"):
        return _empty_node_summary(config.environment_id, str(target_summary.get("status")), target_summary)

    cpu = _query_scalar(config, '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)')
    memory = _query_scalar(config, '(1 - (sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))) * 100')
    disk = _query_scalar(config, '(1 - (sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}) / sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}))) * 100')
    network = _query_scalar(config, 'sum(rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m]))')

    return {
        "environment_id": config.environment_id,
        "status": "healthy" if target_summary.get("node_exporter_present") else "missing",
        "node_exporter_present": target_summary.get("node_exporter_present"),
        "node_exporter_up_count": target_summary.get("node_exporter_up_count"),
        "cpu_pressure_percent": cpu,
        "memory_pressure_percent": memory,
        "disk_pressure_percent": disk,
        "network_bytes_per_second": network,
    }


def get_environment_metrics(environment_id: str | None = None) -> dict[str, object]:
    """Return a safe read-only Prometheus rollup for one environment."""
    config = get_prometheus_config(environment_id)
    health = get_prometheus_health(environment_id)
    target_summary = get_target_summary(environment_id)
    node_summary = get_node_summary(environment_id)
    return {
        "environment_id": config["environment_id"],
        "config": config,
        "health": health,
        "target_summary": target_summary,
        "node_summary": node_summary,
    }


def get_all_environments() -> list[str]:
    """Return all configured environment IDs."""
    return list(PROMETHEUS_CONFIGS.keys())


def _config_for(environment_id: str | None) -> PrometheusSourceConfig | None:
    if not PROMETHEUS_CONFIGS:
        return None
    if environment_id and environment_id in PROMETHEUS_CONFIGS:
        return PROMETHEUS_CONFIGS[str(environment_id)]
    if PRIMARY_ENVIRONMENT_ID in PROMETHEUS_CONFIGS:
        return PROMETHEUS_CONFIGS[PRIMARY_ENVIRONMENT_ID]
    return next(iter(PROMETHEUS_CONFIGS.values()))


def _request_json(config: PrometheusSourceConfig, path: str, params: dict[str, str]) -> dict[str, Any]:
    query = urlencode(params)
    url = f"{config.base_url.rstrip('/')}{path}?{query}"
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


def _query_scalar(config: PrometheusSourceConfig, query: str) -> float | None:
    response = _request_json(config, "/api/v1/query", {"query": query})
    if not response["ok"]:
        return None

    results = response["data"].get("data", {}).get("result", [])
    if not results:
        return None

    value = results[0].get("value", [])
    if len(value) < 2:
        return None
    try:
        return round(float(value[1]), 2)
    except (TypeError, ValueError):
        return None


def _is_node_exporter_target(target: dict[str, Any]) -> bool:
    labels = target.get("labels", {})
    discovered = target.get("discoveredLabels", {})
    values = " ".join(str(v).lower() for v in [*labels.values(), *discovered.values()])
    return "node" in values or "9100" in values


def _target_label(target: dict[str, Any]) -> str:
    labels = target.get("labels", {})
    discovered = target.get("discoveredLabels", {})
    return str(labels.get("instance") or discovered.get("__address__") or target.get("scrapeUrl") or "unknown-target")


def _empty_target_summary(environment_id: str, status: str) -> dict[str, object]:
    return {
        "environment_id": environment_id,
        "status": status,
        "active_target_count": 0,
        "up_target_count": 0,
        "down_target_count": 0,
        "node_exporter_present": False,
        "node_exporter_up_count": 0,
        "down_targets": [],
        "message": "No Prometheus target data available.",
    }


def _empty_node_summary(environment_id: str, status: str, target_summary: dict[str, object]) -> dict[str, object]:
    return {
        "environment_id": environment_id,
        "status": status,
        "node_exporter_present": target_summary.get("node_exporter_present", False),
        "node_exporter_up_count": target_summary.get("node_exporter_up_count", 0),
        "cpu_pressure_percent": None,
        "memory_pressure_percent": None,
        "disk_pressure_percent": None,
        "network_bytes_per_second": None,
    }
