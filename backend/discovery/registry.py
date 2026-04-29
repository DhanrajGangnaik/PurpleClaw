"""
In-memory service registry shared between the discovery and threat engines.

The registry is the single source of truth for what services have been found
on the network. Discovery writes to it; the threat engine reads from it.
Both engines also seed it from env vars (for explicitly configured services).
"""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("purpleclaw.registry")

_LOCK = threading.Lock()
_REGISTRY: dict[str, "ServiceEntry"] = {}


@dataclass
class ServiceEntry:
    host: str
    port: int
    service_type: str         # "prometheus", "loki", "kubernetes", "grafana", etc.
    display_name: str
    url: str | None           # Full base URL if HTTP-reachable
    confirmed: bool           # True if fingerprinting confirmed the type
    last_seen: datetime
    metadata: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def key(self) -> str:
        return f"{self.host}:{self.port}"


# ── Registry operations ───────────────────────────────────────────────────────

def upsert(entry: ServiceEntry) -> bool:
    """
    Add or refresh a service entry. Returns True if this was a new entry.
    """
    k = entry.key()
    with _LOCK:
        existing = _REGISTRY.get(k)
        if existing:
            existing.last_seen = entry.last_seen
            existing.confirmed = existing.confirmed or entry.confirmed
            if entry.url and not existing.url:
                existing.url = entry.url
            # Upgrade service_type from generic to specific
            if entry.service_type not in ("unknown", "http", "tcp") or existing.service_type in ("unknown", "tcp"):
                existing.service_type = entry.service_type
                existing.display_name = entry.display_name
            if entry.metadata:
                existing.metadata.update(entry.metadata)
            for t in entry.tags:
                if t not in existing.tags:
                    existing.tags.append(t)
            return False
        _REGISTRY[k] = entry
        return True


def get_by_type(service_type: str) -> list[ServiceEntry]:
    """Return all registry entries matching a service type."""
    with _LOCK:
        return [e for e in _REGISTRY.values() if e.service_type == service_type]


def get_all() -> list[ServiceEntry]:
    with _LOCK:
        return list(_REGISTRY.values())


def get(key: str) -> ServiceEntry | None:
    with _LOCK:
        return _REGISTRY.get(key)


def clear() -> None:
    with _LOCK:
        _REGISTRY.clear()


def snapshot() -> dict:
    """Return a JSON-serialisable snapshot for the /engine/status endpoint."""
    with _LOCK:
        return {
            "total": len(_REGISTRY),
            "by_type": _count_by_type(),
            "services": [
                {
                    "key": e.key(),
                    "host": e.host,
                    "port": e.port,
                    "type": e.service_type,
                    "name": e.display_name,
                    "url": e.url,
                    "confirmed": e.confirmed,
                    "last_seen": e.last_seen.isoformat(),
                    "tags": e.tags,
                }
                for e in sorted(_REGISTRY.values(), key=lambda x: x.service_type)
            ],
        }


def _count_by_type() -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in _REGISTRY.values():
        counts[e.service_type] = counts.get(e.service_type, 0) + 1
    return counts


# ── Env-var seeding ───────────────────────────────────────────────────────────

def seed_from_env() -> int:
    """
    Seed the registry from explicitly configured service URLs in env vars.
    These are treated as confirmed entries so they're used immediately even
    before a network scan completes.
    """
    _ENV_SERVICES = [
        ("PROMETHEUS_URL", "prometheus", "Prometheus"),
        ("LOKI_URL", "loki", "Grafana Loki"),
        ("GRAFANA_URL", "grafana", "Grafana"),
        ("KUBERNETES_URL", "kubernetes", "Kubernetes API"),
        ("OLLAMA_URL", "ollama", "Ollama"),
        ("MLFLOW_URL", "mlflow", "MLflow"),
    ]

    count = 0
    for env_var, svc_type, display in _ENV_SERVICES:
        # Primary URL
        for url in _collect_env_urls(env_var):
            if _add_from_url(url, svc_type, display, tags=["env-configured"]):
                count += 1

    # Multi-env patterns: PROMETHEUS_URL_<NAME>, LOKI_URL_<NAME>
    for prefix, svc_type, display in [
        ("PROMETHEUS_URL_", "prometheus", "Prometheus"),
        ("LOKI_URL_", "loki", "Grafana Loki"),
    ]:
        for k, v in os.environ.items():
            if k.startswith(prefix) and v.strip():
                env_name = k[len(prefix):].lower()
                if _add_from_url(v.strip(), svc_type, f"{display} ({env_name})",
                                 tags=["env-configured", env_name]):
                    count += 1

    return count


def _collect_env_urls(env_var: str) -> list[str]:
    raw = os.getenv(env_var, "").strip()
    return [raw] if raw else []


def _add_from_url(url: str, svc_type: str, display: str, tags: list[str] | None = None) -> bool:
    url = url.rstrip("/")
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        host = p.hostname or ""
        port = p.port or (443 if p.scheme == "https" else 80)
        if not host:
            return False
        entry = ServiceEntry(
            host=host, port=port,
            service_type=svc_type, display_name=display,
            url=url, confirmed=True,
            last_seen=datetime.utcnow(),
            metadata={"source": "env"},
            tags=list(tags or []),
        )
        return upsert(entry)
    except Exception as exc:
        logger.debug("registry: failed to add %s: %s", url, exc)
        return False
