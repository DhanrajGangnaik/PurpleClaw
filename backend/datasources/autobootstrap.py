from __future__ import annotations

import logging
import os

from datasources.jobs.runtime import schedule_datasource_ingestion
from datasources.models import DataSourceCreate
from datasources.store import get_datasource, save_datasource
from persistence.store import create_environment, get_environment

logger = logging.getLogger("purpleclaw.autobootstrap")

_DEFAULT_INTERVAL = 300


def _ensure_environment(env_id: str) -> bool:
    if get_environment(env_id) is not None:
        return True
    try:
        create_environment(env_id, "lab", f"Auto-created environment for {env_id}")
        return True
    except ValueError as exc:
        logger.warning("Could not create environment %s: %s", env_id, exc)
        return False


def _bootstrap_one(
    env_id: str,
    ds_type: str,
    name: str,
    url: str,
    extra_config: dict | None = None,
    interval: int = _DEFAULT_INTERVAL,
) -> None:
    if not url:
        return
    if not _ensure_environment(env_id):
        env_id = "homelab"

    ds_id = f"{env_id}-{ds_type}"
    if get_datasource(ds_id) is not None:
        return

    config: dict = {"url": url.rstrip("/")}
    if extra_config:
        config.update(extra_config)

    try:
        ds = save_datasource(
            DataSourceCreate(
                environment_id=env_id,
                name=name,
                type=ds_type,
                status="enabled",
                config=config,
                ingestion_enabled=True,
                ingestion_interval_seconds=interval,
            ),
            datasource_id=ds_id,
        )
        schedule_datasource_ingestion(ds.datasource_id, "interval", interval, True)
        logger.info("Auto-bootstrapped %s datasource: %s", ds_type, ds_id)
    except Exception as exc:
        logger.warning("Auto-bootstrap failed for %s/%s: %s", env_id, ds_type, exc)


def autobootstrap_from_env() -> None:
    """Create and schedule datasources for every service URL found in env vars."""

    primary_env = os.getenv("PROMETHEUS_ENV_ID", os.getenv("LOKI_ENV_ID", "homelab"))

    # Prometheus
    prom_url = os.getenv("PROMETHEUS_URL", "").strip()
    if prom_url:
        _bootstrap_one(
            primary_env, "prometheus", f"Prometheus ({primary_env})", prom_url,
            {"timeout_seconds": os.getenv("PROMETHEUS_TIMEOUT", "3.0")},
        )

    # Loki
    loki_url = os.getenv("LOKI_URL", "").strip()
    if loki_url:
        _bootstrap_one(
            primary_env, "loki", f"Loki ({primary_env})", loki_url,
            {"timeout_seconds": os.getenv("LOKI_TIMEOUT", "3.0")},
        )

    # Kubernetes
    k8s_url = os.getenv("KUBERNETES_URL", "").strip()
    if k8s_url:
        extra: dict = {"verify_ssl": os.getenv("KUBERNETES_VERIFY_SSL", "true")}
        k8s_token = os.getenv("KUBERNETES_TOKEN", "").strip()
        if k8s_token:
            extra["token"] = k8s_token
        _bootstrap_one(primary_env, "kubernetes", "Kubernetes API", k8s_url, extra)

    # Grafana
    grafana_url = os.getenv("GRAFANA_URL", "").strip()
    if grafana_url:
        extra = {}
        grafana_key = os.getenv("GRAFANA_API_KEY", "").strip()
        if grafana_key:
            extra["api_key"] = grafana_key
        _bootstrap_one(primary_env, "grafana", "Grafana", grafana_url, extra if extra else None)

    # Ollama
    ollama_url = os.getenv("OLLAMA_URL", "").strip()
    if ollama_url:
        _bootstrap_one(primary_env, "ollama", "Ollama", ollama_url)

    # MLflow
    mlflow_url = os.getenv("MLFLOW_URL", "").strip()
    if mlflow_url:
        extra = {}
        mlflow_token = os.getenv("MLFLOW_TOKEN", "").strip()
        if mlflow_token:
            extra["token"] = mlflow_token
        _bootstrap_one(primary_env, "mlflow", "MLflow", mlflow_url, extra if extra else None)

    # Additional named Prometheus environments: PROMETHEUS_URL_<NAME>=...
    for key, val in os.environ.items():
        if key.startswith("PROMETHEUS_URL_") and val.strip():
            extra_env = key[len("PROMETHEUS_URL_"):].lower()
            if extra_env:
                _bootstrap_one(extra_env, "prometheus", f"Prometheus ({extra_env})", val.strip())

    # Additional named Loki environments: LOKI_URL_<NAME>=...
    for key, val in os.environ.items():
        if key.startswith("LOKI_URL_") and val.strip():
            extra_env = key[len("LOKI_URL_"):].lower()
            if extra_env:
                _bootstrap_one(extra_env, "loki", f"Loki ({extra_env})", val.strip())
