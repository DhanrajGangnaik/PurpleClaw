"""
Auto-discovery engine.

Discovers assets from two sources that work together:
  1. Env-configured services (PROMETHEUS_URL, KUBERNETES_URL, etc.)
     — seeded immediately so the tool works out-of-the-box if URLs are set.
  2. Network scanner — pure Python TCP connect + HTTP fingerprinting that
     discovers ANY service reachable from the container, with zero manual config.

All discovered services are stored in the shared registry (discovery.registry)
and then written to the DB as Asset records.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Callable

import httpx
from sqlalchemy.orm import Session

from discovery.network import run_scan
from discovery import registry as svc_registry
from discovery.registry import ServiceEntry
from models import Asset, AssetStatus, AssetType, Criticality

logger = logging.getLogger("purpleclaw.discovery")

_IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


# ── Service-type → asset-type mapping ────────────────────────────────────────

_SVC_TO_ASSET: dict[str, tuple[AssetType, Criticality, list[str]]] = {
    "prometheus":   (AssetType.server,      Criticality.high,     ["monitoring", "prometheus"]),
    "alertmanager": (AssetType.server,      Criticality.medium,   ["monitoring", "alertmanager"]),
    "loki":         (AssetType.server,      Criticality.medium,   ["logging", "loki"]),
    "grafana":      (AssetType.server,      Criticality.medium,   ["observability", "grafana"]),
    "kubernetes":   (AssetType.server,      Criticality.critical, ["kubernetes", "orchestration"]),
    "ollama":       (AssetType.server,      Criticality.medium,   ["ai", "llm", "ollama"]),
    "mlflow":       (AssetType.server,      Criticality.medium,   ["ml-platform", "mlflow"]),
    "elasticsearch":(AssetType.database,    Criticality.high,     ["search", "elasticsearch"]),
    "kibana":       (AssetType.application, Criticality.medium,   ["logging", "kibana"]),
    "influxdb":     (AssetType.database,    Criticality.high,     ["timeseries", "influxdb"]),
    "postgres":     (AssetType.database,    Criticality.high,     ["database", "postgres"]),
    "mysql":        (AssetType.database,    Criticality.high,     ["database", "mysql"]),
    "redis":        (AssetType.database,    Criticality.high,     ["database", "redis"]),
    "mongodb":      (AssetType.database,    Criticality.high,     ["database", "mongodb"]),
    "zookeeper":    (AssetType.server,      Criticality.high,     ["coordination", "zookeeper"]),
    "kafka":        (AssetType.server,      Criticality.high,     ["messaging", "kafka"]),
    "minio":        (AssetType.server,      Criticality.medium,   ["storage", "minio"]),
    "jupyter":      (AssetType.server,      Criticality.medium,   ["notebook", "jupyter"]),
    "docker":       (AssetType.server,      Criticality.critical, ["container", "docker"]),
    "portainer":    (AssetType.application, Criticality.high,     ["container", "portainer"]),
    "rabbitmq":     (AssetType.server,      Criticality.medium,   ["messaging", "rabbitmq"]),
    "neo4j":        (AssetType.database,    Criticality.medium,   ["graph-db", "neo4j"]),
    "ssh":          (AssetType.server,      Criticality.high,     ["ssh"]),
    "http":         (AssetType.application, Criticality.low,      ["http"]),
    "tcp":          (AssetType.server,      Criticality.low,      []),
    "unknown":      (AssetType.server,      Criticality.low,      []),
}


def _asset_type_from_svc(svc_type: str) -> tuple[AssetType, Criticality, list[str]]:
    return _SVC_TO_ASSET.get(svc_type, (AssetType.server, Criticality.low, []))


# ── DB helpers ────────────────────────────────────────────────────────────────

def _upsert_asset(
    db: Session,
    name: str,
    asset_type: AssetType,
    ip_address: str | None = None,
    hostname: str | None = None,
    os_name: str | None = None,
    services: list | None = None,
    criticality: Criticality = Criticality.medium,
    tags: list | None = None,
    notes: str | None = None,
) -> tuple[Asset, bool]:
    existing = None
    if ip_address:
        existing = db.query(Asset).filter(Asset.ip_address == ip_address).first()
    if not existing and hostname:
        existing = db.query(Asset).filter(Asset.hostname == hostname).first()
    if not existing:
        existing = db.query(Asset).filter(Asset.name == name).first()

    now = datetime.utcnow()
    if existing:
        existing.last_seen = now
        if ip_address and not existing.ip_address:
            existing.ip_address = ip_address
        if hostname and not existing.hostname:
            existing.hostname = hostname
        if os_name and not existing.os:
            existing.os = os_name
        if services:
            existing.services = list({s for s in (existing.services or []) + services})
        if tags:
            existing.tags = list({t for t in (existing.tags or []) + tags})
        return existing, False

    asset = Asset(
        name=name,
        type=asset_type,
        ip_address=ip_address,
        hostname=hostname,
        os=os_name,
        status=AssetStatus.active,
        criticality=criticality,
        services=services or [],
        tags=list({*(tags or []), "auto-discovered"}),
        risk_score=0.0,
        last_seen=now,
        notes=notes,
    )
    db.add(asset)
    return asset, True


# ── Registry → DB sync ────────────────────────────────────────────────────────

def _sync_registry_to_db(db: Session) -> int:
    """Write every registry entry to the Asset table. Returns new-asset count."""
    count = 0
    for entry in svc_registry.get_all():
        atype, crit, base_tags = _asset_type_from_svc(entry.service_type)
        is_ip = bool(_IP_RE.match(entry.host))

        tags = base_tags + entry.tags + [entry.service_type]
        svc_label = f"{entry.service_type}/{entry.port}"

        _, is_new = _upsert_asset(
            db,
            name=f"{entry.service_type}@{entry.host}:{entry.port}",
            asset_type=atype,
            ip_address=entry.host if is_ip else None,
            hostname=None if is_ip else entry.host,
            services=[svc_label],
            criticality=crit,
            tags=tags,
            notes=(
                f"{entry.display_name} discovered at {entry.url or entry.host}:{entry.port}. "
                f"Confirmed: {entry.confirmed}. First seen: {entry.last_seen.isoformat()}"
            ),
        )
        if is_new:
            count += 1

    return count


# ── Prometheus-enriched discovery ─────────────────────────────────────────────

def _discover_via_prometheus(db: Session, timeout: float) -> int:
    """
    Query Prometheus /api/v1/targets on every known Prometheus instance
    to discover the services it scrapes.
    """
    count = 0
    for entry in svc_registry.get_by_type("prometheus"):
        if not entry.url:
            continue
        try:
            with httpx.Client(timeout=timeout, verify=False) as client:
                resp = client.get(f"{entry.url}/api/v1/targets")
                if resp.status_code != 200:
                    continue
                active = resp.json().get("data", {}).get("activeTargets", [])
                for target in active:
                    labels = target.get("labels", {})
                    job = labels.get("job", "unknown")
                    instance = labels.get("instance", "")
                    if not instance:
                        continue
                    host = instance.rsplit(":", 1)[0]
                    port = instance.rsplit(":", 1)[1] if ":" in instance else None
                    is_ip = bool(_IP_RE.match(host))

                    atype = AssetType.server
                    jl = job.lower()
                    if any(k in jl for k in ("container", "docker", "cadvisor", "pod")):
                        atype = AssetType.container
                    elif any(k in jl for k in ("database", "mysql", "postgres", "redis", "mongo", "elastic")):
                        atype = AssetType.database
                    elif any(k in jl for k in ("app", "service", "api", "http")):
                        atype = AssetType.application

                    _, is_new = _upsert_asset(
                        db,
                        name=f"{job}@{host}",
                        asset_type=atype,
                        ip_address=host if is_ip else None,
                        hostname=None if is_ip else host,
                        services=[f"{job}/{port}"] if port else [job],
                        tags=["prometheus-target", job],
                        notes=f"Prometheus scrape target. Job: {job}, Instance: {instance}",
                    )
                    if is_new:
                        count += 1
        except Exception as exc:
            logger.debug("Prometheus target discovery failed for %s: %s", entry.url, exc)
    return count


def _discover_via_kubernetes(db: Session, timeout: float) -> int:
    """Query every known Kubernetes API server and discover nodes + services."""
    count = 0
    for entry in svc_registry.get_by_type("kubernetes"):
        if not entry.url:
            continue
        token = os.getenv("KUBERNETES_TOKEN", "").strip()
        verify = os.getenv("KUBERNETES_VERIFY_SSL", "true").lower() not in ("false", "0", "no")
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            with httpx.Client(verify=verify, timeout=timeout) as client:
                resp = client.get(f"{entry.url}/api/v1/nodes", headers=headers)
                if resp and resp.status_code == 200:
                    for node in resp.json().get("items", []):
                        meta = node.get("metadata", {})
                        status = node.get("status", {})
                        addrs = {a["type"]: a["address"] for a in status.get("addresses", [])}
                        labels = meta.get("labels", {})
                        is_cp = any(k in labels for k in (
                            "node-role.kubernetes.io/control-plane",
                            "node-role.kubernetes.io/master",
                        ))
                        node_info = status.get("nodeInfo", {})
                        _, is_new = _upsert_asset(
                            db,
                            name=f"k8s-node:{meta.get('name', 'unknown')}",
                            asset_type=AssetType.server,
                            ip_address=addrs.get("InternalIP") or addrs.get("ExternalIP"),
                            hostname=addrs.get("Hostname") or meta.get("name"),
                            os_name=node_info.get("osImage"),
                            criticality=Criticality.critical if is_cp else Criticality.high,
                            tags=["kubernetes", "node", "control-plane" if is_cp else "worker"],
                        )
                        if is_new:
                            count += 1

                # Exposed services
                resp = client.get(f"{entry.url}/api/v1/services", headers=headers)
                if resp and resp.status_code == 200:
                    for svc in resp.json().get("items", []):
                        meta = svc.get("metadata", {})
                        spec = svc.get("spec", {})
                        svc_type = spec.get("type", "ClusterIP")
                        if svc_type not in ("LoadBalancer", "NodePort"):
                            continue
                        ns = meta.get("namespace", "default")
                        svc_name = meta.get("name", "unknown")
                        ports = [f"{p.get('port')}/{p.get('protocol','TCP')}" for p in spec.get("ports", [])]
                        _, is_new = _upsert_asset(
                            db,
                            name=f"k8s-svc:{ns}/{svc_name}",
                            asset_type=AssetType.application,
                            services=ports,
                            criticality=Criticality.high if svc_type == "LoadBalancer" else Criticality.medium,
                            tags=["kubernetes", "service", svc_type.lower(), ns],
                        )
                        if is_new:
                            count += 1
        except Exception as exc:
            logger.debug("K8s discovery failed for %s: %s", entry.url, exc)
    return count


def _discover_via_loki(db: Session, timeout: float) -> int:
    """Discover unique log sources from every known Loki instance."""
    count = 0
    for entry in svc_registry.get_by_type("loki"):
        if not entry.url:
            continue
        try:
            with httpx.Client(timeout=timeout, verify=False) as client:
                for label in ("job", "service_name", "app", "container", "host"):
                    resp = client.get(f"{entry.url}/loki/api/v1/label/{label}/values")
                    if not resp or resp.status_code != 200:
                        continue
                    for value in resp.json().get("data", []):
                        if not value or value in ("", "null", "unknown"):
                            continue
                        _, is_new = _upsert_asset(
                            db,
                            name=f"log-source:{value}",
                            asset_type=AssetType.application,
                            criticality=Criticality.low,
                            tags=["loki", label, value],
                            notes=f"Log source from Loki label {label}={value}",
                        )
                        if is_new:
                            count += 1
        except Exception as exc:
            logger.debug("Loki discovery failed for %s: %s", entry.url, exc)
    return count


# ── Engine ────────────────────────────────────────────────────────────────────

class DiscoveryEngine:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._timeout = float(os.getenv("DISCOVERY_TIMEOUT", "8"))
        self._scan_enabled = os.getenv("SCAN_NETWORK", "true").lower() not in ("false", "0", "no")

    def run(self) -> dict[str, int]:
        """
        Full discovery cycle:
        1. Seed registry from env vars (fast, immediate)
        2. Network scan (finds anything not in env vars)
        3. Enrich from known services (Prometheus targets, K8s nodes, Loki streams)
        4. Sync registry to DB
        """
        results: dict[str, int] = {
            "env_seeds": 0,
            "network_scan": 0,
            "prometheus_targets": 0,
            "kubernetes_nodes": 0,
            "loki_sources": 0,
            "new_assets": 0,
        }

        # Step 1: env seeding
        results["env_seeds"] = svc_registry.seed_from_env()

        # Step 2: network scan
        if self._scan_enabled:
            try:
                scan_results = run_scan()
                for r in scan_results:
                    entry = ServiceEntry(
                        host=r.host, port=r.port,
                        service_type=r.service_type,
                        display_name=r.display_name,
                        url=r.url,
                        confirmed=r.confirmed,
                        last_seen=r.last_seen,
                        metadata=r.metadata,
                        tags=["network-scan"],
                    )
                    if svc_registry.upsert(entry):
                        results["network_scan"] += 1
            except Exception as exc:
                logger.error("Network scan failed: %s", exc)
        else:
            logger.info("Network scanning disabled (SCAN_NETWORK=false)")

        # Step 3: enrich via known service APIs
        db = self._session_factory()
        try:
            results["prometheus_targets"] = _discover_via_prometheus(db, self._timeout)
            results["kubernetes_nodes"] = _discover_via_kubernetes(db, self._timeout)
            results["loki_sources"] = _discover_via_loki(db, self._timeout)

            # Step 4: sync all registry entries to DB
            results["new_assets"] = _sync_registry_to_db(db)

            db.commit()
            total = sum(v for v in results.values())
            if total > 0:
                logger.info("Discovery cycle complete: %s", results)
        except Exception as exc:
            db.rollback()
            logger.error("Discovery DB error: %s", exc)
        finally:
            db.close()

        return results
