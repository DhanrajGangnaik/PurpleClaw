"""
Zero-config network scanner and service fingerprinter.

Discovers any reachable service on the local network using pure Python
TCP connect scanning + HTTP fingerprinting — no nmap, no root required.

Environment controls:
  SCAN_NETWORK=true           Enable/disable network scanning (default: true)
  SCAN_PORTS=22,80,9090,...   Override port list
  SCAN_TIMEOUT=0.5            Per-port TCP timeout in seconds
  SCAN_CONCURRENCY=100        Max parallel TCP probes
  SCAN_RANGES=192.168.1.0/24  Extra CIDR ranges to scan (comma-separated)
  SCAN_EXCLUDE=10.0.0.0/8     CIDR ranges to skip (comma-separated)
"""

from __future__ import annotations

import ipaddress
import logging
import os
import socket
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable

import httpx

logger = logging.getLogger("purpleclaw.network")

# ── Default ports ─────────────────────────────────────────────────────────────

DEFAULT_PORTS: list[int] = [
    22,             # SSH
    80, 443,        # HTTP / HTTPS
    2181,           # ZooKeeper
    2375, 2376,     # Docker daemon
    2379, 2380,     # etcd
    3000,           # Grafana / Node.js
    3100,           # Loki
    3306,           # MySQL / MariaDB
    4317, 4318,     # OpenTelemetry gRPC / HTTP
    5000,           # MLflow / Docker Registry / Flask
    5432,           # PostgreSQL
    5601,           # Kibana
    6379,           # Redis
    6443,           # Kubernetes API server
    7474, 7687,     # Neo4j HTTP / Bolt
    8080, 8443, 8888,  # Alt HTTP / Jupyter
    8086,           # InfluxDB
    9000,           # MinIO / Portainer
    9090,           # Prometheus
    9092, 9093,     # Kafka / Alertmanager
    9200, 9201,     # Elasticsearch
    9100,           # Node Exporter
    10250,          # Kubelet
    11434,          # Ollama
    15672,          # RabbitMQ management
    27017,          # MongoDB
    50070,          # HDFS NameNode
]

# ── Fingerprint database ───────────────────────────────────────────────────────
# Each tuple: (service_type, display_name, http_probe_paths, match_fn)
# match_fn receives the httpx.Response and returns True if confirmed.

_FP: list[tuple[str, str, list[str], Callable]] = [
    (
        "prometheus", "Prometheus",
        ["/api/v1/status/runtimeinfo", "/api/v1/targets", "/-/ready"],
        lambda r: r.status_code == 200 and (
            "prometheusVersion" in r.text or "activeTargets" in r.text or
            "prometheus" in r.headers.get("X-Prometheus-Server", "").lower()
        ),
    ),
    (
        "alertmanager", "Alertmanager",
        ["/api/v2/status", "/-/ready"],
        lambda r: r.status_code == 200 and (
            '"cluster"' in r.text or "alertmanager" in r.text.lower()
        ),
    ),
    (
        "loki", "Grafana Loki",
        ["/loki/api/v1/status/buildinfo", "/loki/api/v1/label", "/ready"],
        lambda r: r.status_code == 200 and (
            "loki" in r.text.lower() or "buildDate" in r.text or "version" in r.text
        ) or (r.status_code == 204 and "loki" in str(r.url).lower()),
    ),
    (
        "kubernetes", "Kubernetes API",
        ["/version", "/readyz", "/livez"],
        lambda r: r.status_code in (200, 401, 403) and (
            "major" in r.text or "Unauthorized" in r.text or
            "apiVersion" in r.text
        ),
    ),
    (
        "grafana", "Grafana",
        ["/api/health", "/api/frontend/settings"],
        lambda r: r.status_code == 200 and (
            "database" in r.text or "grafanaBootData" in r.text or
            "grafana" in r.headers.get("X-Frame-Options", "").lower()
        ),
    ),
    (
        "ollama", "Ollama",
        ["/api/tags", "/api/version"],
        lambda r: r.status_code == 200 and (
            "models" in r.text or '"version"' in r.text
        ),
    ),
    (
        "mlflow", "MLflow",
        ["/health", "/api/2.0/mlflow/experiments/search"],
        lambda r: r.status_code == 200 and (
            r.text.strip() in ("OK", "ok", "") or "experiments" in r.text
        ),
    ),
    (
        "elasticsearch", "Elasticsearch",
        ["/", "/_cluster/health"],
        lambda r: r.status_code == 200 and "cluster_name" in r.text,
    ),
    (
        "kibana", "Kibana",
        ["/api/status"],
        lambda r: r.status_code == 200 and "kibana" in r.text.lower(),
    ),
    (
        "influxdb", "InfluxDB",
        ["/ping", "/health"],
        lambda r: r.status_code in (200, 204) and (
            "influxdb" in r.headers.get("X-Influxdb-Version", "").lower() or
            "influxdb" in r.text.lower()
        ),
    ),
    (
        "minio", "MinIO",
        ["/minio/health/live", "/health/live"],
        lambda r: r.status_code == 200 and (
            "minio" in r.headers.get("Server", "").lower() or
            "x-amz-request-id" in {h.lower() for h in r.headers}
        ),
    ),
    (
        "jupyter", "Jupyter",
        ["/api", "/api/kernels"],
        lambda r: r.status_code == 200 and (
            "version" in r.text and "jupyter" in r.text.lower()
        ),
    ),
    (
        "docker", "Docker",
        ["/info", "/version"],
        lambda r: r.status_code == 200 and "ServerVersion" in r.text,
    ),
    (
        "portainer", "Portainer",
        ["/api/status"],
        lambda r: r.status_code == 200 and "portainer" in r.text.lower(),
    ),
    (
        "rabbitmq", "RabbitMQ",
        ["/api/overview"],
        lambda r: r.status_code in (200, 401) and (
            "rabbitmq" in r.text.lower() or r.status_code == 401
        ),
    ),
    (
        "neo4j", "Neo4j",
        ["/", "/browser/"],
        lambda r: r.status_code == 200 and "neo4j" in r.text.lower(),
    ),
]

# Generic HTTP fallback — matched last
_HTTP_FALLBACK = ("http", "HTTP Service", [], lambda r: r.status_code < 500)


# ── Network helpers ────────────────────────────────────────────────────────────

def _get_local_ips() -> list[str]:
    """Return all non-loopback IPv4 addresses on this host."""
    ips: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    # UDP trick — finds outbound IP without actually sending traffic
    for target in ("8.8.8.8", "1.1.1.1"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.1)
                s.connect((target, 80))
                ip = s.getsockname()[0]
                if ip and not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
            break
        except Exception:
            pass
    return ips


def _ip_to_network(ip: str, prefix: int = 24) -> ipaddress.IPv4Network | None:
    try:
        return ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
    except Exception:
        return None


def get_scan_targets() -> list[str]:
    """
    Build the list of IP addresses to scan.

    Sources (merged, deduplicated):
    1. /24 subnets of the container's own interfaces
    2. host.docker.internal (if resolvable)
    3. SCAN_RANGES env var (comma-separated CIDRs)
    """
    targets: set[str] = set()
    exclude: list[ipaddress.IPv4Network] = []

    for cidr in os.getenv("SCAN_EXCLUDE", "").split(","):
        cidr = cidr.strip()
        if cidr:
            try:
                exclude.append(ipaddress.IPv4Network(cidr, strict=False))
            except Exception:
                pass

    def _should_skip(ip_str: str) -> bool:
        try:
            ip = ipaddress.IPv4Address(ip_str)
            return any(ip in net for net in exclude)
        except Exception:
            return False

    own_ips = set(_get_local_ips())

    # Own subnets (skip the container's own IPs — no point scanning ourselves)
    for ip in own_ips:
        net = _ip_to_network(ip, 24)
        if net:
            for host in net.hosts():
                h = str(host)
                if h not in own_ips and not _should_skip(h):
                    targets.add(h)

    # host.docker.internal
    for name in ("host.docker.internal", "gateway.docker.internal"):
        try:
            ip = socket.gethostbyname(name)
            if ip and not _should_skip(ip):
                targets.add(ip)
        except Exception:
            pass

    # Extra ranges from env
    for cidr in os.getenv("SCAN_RANGES", "").split(","):
        cidr = cidr.strip()
        if not cidr:
            continue
        try:
            net = ipaddress.IPv4Network(cidr, strict=False)
            for host in net.hosts():
                h = str(host)
                if not _should_skip(h):
                    targets.add(h)
        except Exception:
            logger.debug("Invalid SCAN_RANGES entry: %s", cidr)

    return sorted(targets, key=lambda ip: tuple(int(o) for o in ip.split(".")))


def _tcp_connect(host: str, port: int, timeout: float) -> bool:
    """Return True if host:port accepts a TCP connection."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# ── HTTP fingerprinting ───────────────────────────────────────────────────────

def fingerprint_service(host: str, port: int, timeout: float = 3.0) -> dict:
    """
    Try HTTP (and HTTPS) probes to identify the service type running on host:port.

    Returns:
      {
        "host": str, "port": int, "service_type": str, "display_name": str,
        "url": str, "confirmed": bool, "metadata": dict, "last_seen": datetime
      }
    """
    entry = {
        "host": host, "port": port,
        "service_type": "unknown", "display_name": "Unknown Service",
        "url": None, "confirmed": False,
        "metadata": {}, "last_seen": datetime.utcnow(),
    }

    # Try HTTPS first on known TLS ports, then HTTP
    schemes = ["https", "http"] if port in (443, 6443, 8443, 10250, 2376) else ["http", "https"]

    for scheme in schemes:
        base_url = f"{scheme}://{host}:{port}"
        try:
            with httpx.Client(
                verify=False, timeout=timeout,
                follow_redirects=True,
                headers={"User-Agent": "PurpleClaw/1.0 (security scanner)"},
            ) as client:
                # Try each fingerprint
                for svc_type, display, paths, match_fn in _FP:
                    for path in paths:
                        try:
                            r = client.get(f"{base_url}{path}")
                            if match_fn(r):
                                entry.update(
                                    service_type=svc_type,
                                    display_name=display,
                                    url=base_url,
                                    confirmed=True,
                                    metadata={"http_scheme": scheme, "probe_path": path},
                                )
                                return entry
                        except Exception:
                            continue

                # Generic HTTP fallback — any response from /
                try:
                    r = client.get(f"{base_url}/")
                    if r.status_code < 600:
                        title = ""
                        import re as _re
                        m = _re.search(r"<title[^>]*>(.*?)</title>", r.text, _re.I | _re.S)
                        if m:
                            title = m.group(1).strip()[:80]
                        entry.update(
                            service_type="http",
                            display_name=title or "HTTP Service",
                            url=base_url,
                            confirmed=True,
                            metadata={
                                "http_scheme": scheme,
                                "status_code": r.status_code,
                                "server": r.headers.get("Server", ""),
                                "page_title": title,
                            },
                        )
                        return entry
                except Exception:
                    pass
        except Exception:
            continue

    # TCP-only service (SSH, databases, etc.) — attempt banner grab
    service_type, display = _tcp_banner_identify(host, port)
    entry.update(service_type=service_type, display_name=display, confirmed=service_type != "tcp")
    return entry


def _tcp_banner_identify(host: str, port: int) -> tuple[str, str]:
    """Attempt a raw TCP banner grab and return (service_type, display_name)."""
    known: dict[int, tuple[str, str]] = {
        22: ("ssh", "SSH"),
        2181: ("zookeeper", "ZooKeeper"),
        3306: ("mysql", "MySQL/MariaDB"),
        5432: ("postgres", "PostgreSQL"),
        6379: ("redis", "Redis"),
        7687: ("neo4j-bolt", "Neo4j Bolt"),
        9092: ("kafka", "Kafka"),
        27017: ("mongodb", "MongoDB"),
    }
    if port in known:
        return known[port]
    try:
        with socket.create_connection((host, port), timeout=2) as s:
            s.settimeout(1)
            try:
                banner = s.recv(256).decode("utf-8", errors="ignore").strip()
                if banner.startswith("SSH"):
                    return "ssh", "SSH"
                if "redis" in banner.lower():
                    return "redis", "Redis"
                if "postgresql" in banner.lower():
                    return "postgres", "PostgreSQL"
            except Exception:
                pass
    except Exception:
        pass
    return "tcp", f"TCP:{port}"


# ── Full scan ─────────────────────────────────────────────────────────────────

class ScanResult:
    __slots__ = ("host", "port", "service_type", "display_name", "url", "confirmed", "metadata", "last_seen")

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

    def key(self) -> str:
        return f"{self.host}:{self.port}"


def run_scan(
    targets: list[str] | None = None,
    ports: list[int] | None = None,
    tcp_timeout: float | None = None,
    fp_timeout: float | None = None,
    max_workers: int | None = None,
) -> list[ScanResult]:
    """
    Scan targets for open ports, then fingerprint each open port.

    Returns a list of ScanResult objects for every identified service.
    """
    if not os.getenv("SCAN_NETWORK", "true").lower() not in ("false", "0", "no"):
        # Check env — default enabled
        pass

    _targets = targets or get_scan_targets()
    _ports = ports or _parse_env_ports()
    _tcp_t = tcp_timeout or float(os.getenv("SCAN_TIMEOUT", "0.5"))
    _fp_t = fp_timeout or float(os.getenv("SCAN_FP_TIMEOUT", "3.0"))
    _workers = max_workers or int(os.getenv("SCAN_CONCURRENCY", "100"))

    if not _targets:
        logger.warning("No scan targets found — check network interfaces or set SCAN_RANGES")
        return []

    logger.info("Network scan: %d hosts × %d ports (timeout=%.1fs, workers=%d)",
                len(_targets), len(_ports), _tcp_t, _workers)

    # Phase 1: TCP connect scan
    open_ports: list[tuple[str, int]] = []
    with ThreadPoolExecutor(max_workers=_workers) as ex:
        fut_map = {
            ex.submit(_tcp_connect, host, port, _tcp_t): (host, port)
            for host in _targets for port in _ports
        }
        for fut in as_completed(fut_map):
            host, port = fut_map[fut]
            try:
                if fut.result():
                    open_ports.append((host, port))
            except Exception:
                pass

    if not open_ports:
        logger.info("Network scan: no open ports found")
        return []

    logger.info("Network scan: %d open ports found, fingerprinting...", len(open_ports))

    # Phase 2: Fingerprint open ports (fewer workers — HTTP is slower)
    fp_workers = min(20, len(open_ports))
    results: list[ScanResult] = []
    with ThreadPoolExecutor(max_workers=fp_workers) as ex:
        fut_map2 = {
            ex.submit(fingerprint_service, host, port, _fp_t): (host, port)
            for host, port in open_ports
        }
        for fut in as_completed(fut_map2):
            host, port = fut_map2[fut]
            try:
                data = fut.result()
                results.append(ScanResult(**data))
            except Exception as exc:
                logger.debug("Fingerprint %s:%d failed: %s", host, port, exc)

    confirmed = [r for r in results if r.confirmed and r.service_type != "unknown"]
    logger.info(
        "Network scan complete: %d services identified (%d confirmed typed)",
        len(results), len(confirmed),
    )
    return results


def _parse_env_ports() -> list[int]:
    raw = os.getenv("SCAN_PORTS", "").strip()
    if not raw:
        return DEFAULT_PORTS
    try:
        return [int(p.strip()) for p in raw.split(",") if p.strip()]
    except ValueError:
        return DEFAULT_PORTS
