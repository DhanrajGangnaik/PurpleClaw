"""
Autonomous threat detection and response engine.

Reads from the shared service registry (discovery.registry) to find every
Prometheus, Loki, Kubernetes, and other service discovered on the network.
Runs detectors against all of them — no hardcoded URLs, no env-var gating.
If no services are yet in the registry, seeds it from env vars first.

Detection coverage:
  - Prometheus: firing alerts + metric anomalies (CPU/memory/disk/load/network)
  - Loki: brute-force auth, privilege escalation, SSH scanning, web attacks,
          malware/reverse shells, service crashes and OOM kills
  - Kubernetes: crash loops, privileged containers, image pull failures,
                new cluster-admin bindings
  - Generic: newly discovered network assets (possible lateral movement)
  - Auto-escalation: critical alerts → Incidents
  - Auto-response (optional): iptables block of external attacker IPs
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta
from typing import Callable

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from discovery import registry as svc_registry
from models import (
    Alert, AlertSeverity, AlertStatus,
    Asset, AssetStatus,
    Finding, FindingStatus,
    Incident, IncidentSeverity, IncidentStatus,
    Severity,
)

logger = logging.getLogger("purpleclaw.threats")

_IP_RE = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")

AUTO_RESPONSE = os.getenv("AUTO_RESPONSE", "false").lower() in ("true", "1", "yes")
AUTO_RESPONSE_LEVEL = os.getenv("AUTO_RESPONSE_LEVEL", "safe")


# ── DB helpers ────────────────────────────────────────────────────────────────

def _open_alert(db: Session, rule_name: str) -> Alert | None:
    return db.query(Alert).filter(
        Alert.rule_name == rule_name,
        Alert.status == AlertStatus.open,
    ).first()


def _open_finding(db: Session, title: str, asset_id: int | None) -> Finding | None:
    q = db.query(Finding).filter(Finding.title == title, Finding.status == FindingStatus.open)
    if asset_id:
        q = q.filter(Finding.asset_id == asset_id)
    return q.first()


def _make_alert(
    db: Session, *, title: str, description: str,
    severity: AlertSeverity, source: str, rule_name: str,
    raw_data: dict | None = None, mitre: list | None = None,
) -> Alert | None:
    if _open_alert(db, rule_name):
        return None
    alert = Alert(
        title=title, description=description,
        severity=severity, status=AlertStatus.open,
        source=source, rule_name=rule_name,
        raw_data=raw_data or {},
        mitre_techniques=mitre or [],
        asset_ids=[],
    )
    db.add(alert)
    return alert


def _make_finding(
    db: Session, *, title: str, description: str,
    severity: Severity, source: str,
    asset_id: int | None = None, evidence: str = "",
    remediation: str = "", mitre: list | None = None,
) -> Finding | None:
    if _open_finding(db, title, asset_id):
        return None
    risk = {"critical": 9.5, "high": 7.5, "medium": 4.5, "low": 2.0, "info": 0.5}.get(
        severity.value, 4.0
    )
    finding = Finding(
        title=title, description=description,
        severity=severity, status=FindingStatus.open,
        source=source, asset_id=asset_id,
        evidence=[evidence] if evidence else [],
        remediation=remediation,
        risk_score=risk,
        mitre_techniques=mitre or [],
    )
    db.add(finding)
    return finding


def _asset_for_host(db: Session, host: str) -> Asset | None:
    h = host.split(":")[0]
    return db.query(Asset).filter(
        or_(Asset.hostname == h, Asset.ip_address == h,
            Asset.hostname == host, Asset.ip_address == host)
    ).first()


# ── Prometheus detectors ──────────────────────────────────────────────────────

_METRIC_CHECKS = [
    (
        '100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
        92, Severity.high,
        "Critical CPU pressure on {instance} ({val:.0f}%)",
        "top -b -n1 | head -20  &&  ps aux --sort=-%cpu | head -10",
        ["T1498"],
    ),
    (
        '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
        92, Severity.high,
        "Critical memory pressure on {instance} ({val:.0f}%)",
        "ps aux --sort=-%mem | head -10",
        [],
    ),
    (
        '(1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|devtmpfs|squashfs"} '
        '/ node_filesystem_size_bytes{fstype!~"tmpfs|overlay|devtmpfs|squashfs"})) * 100',
        90, Severity.high,
        "Disk full on {instance} at {mountpoint} ({val:.0f}%)",
        "du -sh /* 2>/dev/null | sort -rh | head -10  ||  journalctl --vacuum-size=1G",
        [],
    ),
    (
        'node_load15 / on(instance) group_left '
        'count without(cpu,mode)(node_cpu_seconds_total{mode="idle"})',
        3.0, Severity.medium,
        "Sustained high load on {instance} ({val:.1f}x CPU count)",
        "uptime && ps aux --sort=-pcpu | head -20",
        [],
    ),
    (
        'rate(node_network_receive_bytes_total[5m]) > 100000000',
        0, Severity.medium,
        "Unusual inbound network on {instance} ({val:.0f} B/s)",
        "ss -tnp  ||  iftop -n",
        ["T1071"],
    ),
]


def _detect_on_prometheus(db: Session, url: str, source_label: str, timeout: float) -> int:
    count = 0
    try:
        with httpx.Client(timeout=timeout, verify=False) as client:
            # Firing alerts
            resp = client.get(f"{url}/api/v1/alerts")
            if resp.status_code == 200:
                for a in resp.json().get("data", {}).get("alerts", []):
                    if a.get("state") != "firing":
                        continue
                    labels = a.get("labels", {})
                    ann = a.get("annotations", {})
                    name = labels.get("alertname", "UnknownAlert")
                    summary = ann.get("summary") or ann.get("message") or name
                    desc = ann.get("description") or summary
                    raw_sev = labels.get("severity", "warning").lower()
                    sev = (AlertSeverity.critical if raw_sev in ("critical", "page")
                           else AlertSeverity.high if raw_sev in ("warning", "error")
                           else AlertSeverity.medium)
                    if _make_alert(
                        db,
                        title=f"[{source_label}] {name}: {summary}",
                        description=desc, severity=sev,
                        source=source_label, rule_name=f"prom:{name}:{url}",
                        raw_data=a,
                    ):
                        count += 1

            # Metric anomalies
            for query, threshold, sev, title_tpl, remediation, mitre in _METRIC_CHECKS:
                try:
                    resp = client.get(f"{url}/api/v1/query", params={"query": query})
                    if resp.status_code != 200:
                        continue
                    for result in resp.json().get("data", {}).get("result", []):
                        val = float(result.get("value", [0, 0])[1])
                        if threshold > 0 and val < threshold:
                            continue
                        metric = result.get("metric", {})
                        instance = metric.get("instance", "unknown")
                        mountpoint = metric.get("mountpoint", "")
                        asset = _asset_for_host(db, instance)
                        title = title_tpl.format(instance=instance, val=val, mountpoint=mountpoint)
                        if _make_finding(
                            db, title=title,
                            description=f"Measured: {val:.2f} (threshold: {threshold}). Host: {instance}",
                            severity=sev, source=f"{source_label}/Auto",
                            asset_id=asset.id if asset else None,
                            evidence=f"PromQL={query!r} → {val:.2f} on {instance}",
                            remediation=remediation, mitre=mitre,
                        ):
                            count += 1
                except Exception:
                    pass
    except Exception as exc:
        logger.debug("Prometheus detect failed for %s: %s", url, exc)
    return count


# ── Loki detectors ────────────────────────────────────────────────────────────

_AUTH_PATTERNS = [
    (
        '{job=~".+"} |~ "(?i)(failed password|authentication failure|invalid user|failed login|auth failure|incorrect password)"',
        10, AlertSeverity.critical,
        "Brute-force authentication attack detected",
        ["T1110", "T1110.001"],
    ),
    (
        '{job=~".+"} |~ "(?i)(sudo.*authentication failure|sudo.*incorrect password|su:.*FAILED)"',
        3, AlertSeverity.critical,
        "Privilege escalation attempt via sudo/su",
        ["T1548", "T1548.003"],
    ),
    (
        '{job=~".+"} |~ "(?i)(ssh.*invalid|sshd.*error|connection closed|did not receive identification)"',
        20, AlertSeverity.high,
        "SSH scanning or connection probing detected",
        ["T1021.004", "T1595"],
    ),
    (
        '{job=~".+"} |~ "(?i)(web.*attack|sql.*injection|xss|path.*traversal|\\.\\./)"',
        3, AlertSeverity.critical,
        "Web application attack detected",
        ["T1190", "T1059.007"],
    ),
    (
        '{job=~".+"} |~ "(?i)(nmap|masscan|nikto|nuclei|dirscan|gobuster|dirb)"',
        1, AlertSeverity.high,
        "Network or vulnerability scanner detected",
        ["T1595", "T1046"],
    ),
    (
        '{job=~".+"} |~ "(?i)(malware|ransomware|trojan|backdoor|rootkit|reverse shell|netcat|/bin/sh|/bin/bash.*-i|nc -e)"',
        1, AlertSeverity.critical,
        "Potential malware or reverse-shell activity",
        ["T1059", "T1071"],
    ),
]


def _detect_on_loki(db: Session, url: str, source_label: str, timeout: float) -> int:
    now = datetime.utcnow()
    start_ns = int((now - timedelta(minutes=15)).timestamp() * 1e9)
    end_ns = int(now.timestamp() * 1e9)
    count = 0

    try:
        with httpx.Client(timeout=timeout, verify=False) as client:
            # Auth / attack patterns
            for logql, threshold, sev, title, mitre in _AUTH_PATTERNS:
                try:
                    resp = client.get(
                        f"{url}/loki/api/v1/query_range",
                        params={"query": logql, "start": start_ns, "end": end_ns,
                                "limit": 500, "direction": "backward"},
                    )
                    if resp.status_code != 200:
                        continue
                    streams = resp.json().get("data", {}).get("result", [])
                    total = sum(len(s.get("values", [])) for s in streams)
                    if total < threshold:
                        continue

                    ips: set[str] = set()
                    sample_lines: list[str] = []
                    for stream in streams[:5]:
                        for _, line in stream.get("values", [])[:3]:
                            for m in _IP_RE.finditer(line):
                                ips.add(m.group(1))
                            sample_lines.append(line[:200])

                    ip_note = f" Source IPs: {', '.join(list(ips)[:8])}." if ips else ""
                    rule = f"loki:{title.lower().replace(' ', '-')}:{url}"
                    if _make_alert(
                        db,
                        title=f"[{source_label}] {title}",
                        description=(
                            f"{total} matching events in 15 min.{ip_note}\n"
                            f"Sample: {sample_lines[0][:300] if sample_lines else 'N/A'}"
                        ),
                        severity=sev, source=f"{source_label}/Auto", rule_name=rule,
                        raw_data={"event_count": total, "source_ips": list(ips)[:20],
                                  "query": logql, "sample": sample_lines[:3]},
                        mitre=mitre,
                    ):
                        count += 1

                    if AUTO_RESPONSE and ips and sev == AlertSeverity.critical:
                        _block_ips(list(ips)[:5], reason=rule)
                except Exception:
                    pass

            # Crash / OOM detection
            now_inner = datetime.utcnow()
            s_ns = int((now_inner - timedelta(minutes=10)).timestamp() * 1e9)
            e_ns = int(now_inner.timestamp() * 1e9)
            try:
                resp = client.get(
                    f"{url}/loki/api/v1/query_range",
                    params={
                        "query": '{job=~".+"} |~ "(?i)(panic|fatal error|segmentation fault|killed|oom killer|out of memory)"',
                        "start": s_ns, "end": e_ns, "limit": 200,
                    },
                )
                if resp.status_code == 200:
                    for stream in resp.json().get("data", {}).get("result", []):
                        job = (stream.get("stream", {}).get("job")
                               or stream.get("stream", {}).get("app")
                               or "unknown")
                        events = len(stream.get("values", []))
                        if events < 1:
                            continue
                        sample = stream["values"][0][1][:300] if stream.get("values") else ""
                        if _make_finding(
                            db,
                            title=f"Service crash/OOM: {job}",
                            description=f"{events} crash/OOM events from '{job}' in 10 min. Sample: {sample}",
                            severity=Severity.critical, source=f"{source_label}/Auto",
                            evidence=f"job={job}, events={events}",
                            remediation=f"kubectl logs <pod> -c {job} --previous  ||  journalctl -u {job} -n 100",
                            mitre=["T1499"],
                        ):
                            count += 1
            except Exception:
                pass
    except Exception as exc:
        logger.debug("Loki detect failed for %s: %s", url, exc)
    return count


# ── Kubernetes detectors ──────────────────────────────────────────────────────

def _detect_on_kubernetes(db: Session, url: str, source_label: str, timeout: float) -> int:
    token = os.getenv("KUBERNETES_TOKEN", "").strip()
    verify = os.getenv("KUBERNETES_VERIFY_SSL", "true").lower() not in ("false", "0", "no")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    count = 0
    try:
        with httpx.Client(verify=verify, timeout=timeout) as client:
            resp = client.get(f"{url}/api/v1/pods", headers=headers)
            if resp.status_code == 200:
                for pod in resp.json().get("items", []):
                    meta = pod.get("metadata", {})
                    status = pod.get("status", {})
                    spec = pod.get("spec", {})
                    ns = meta.get("namespace", "default")
                    pod_name = meta.get("name", "unknown")

                    for cs in status.get("containerStatuses", []):
                        restarts = cs.get("restartCount", 0)
                        waiting = cs.get("state", {}).get("waiting", {})
                        reason = waiting.get("reason", "")
                        cname = cs.get("name", "unknown")

                        if reason == "CrashLoopBackOff" or restarts >= 5:
                            sev = Severity.critical if reason == "CrashLoopBackOff" else Severity.high
                            if _make_finding(
                                db,
                                title=f"K8s CrashLoop: {ns}/{pod_name}/{cname}",
                                description=f"Container {cname} has {restarts} restarts. Reason: {reason or 'high restarts'}",
                                severity=sev, source=f"{source_label}/Auto",
                                evidence=f"ns={ns} pod={pod_name} container={cname} restarts={restarts}",
                                remediation=f"kubectl logs -n {ns} {pod_name} -c {cname} --previous",
                                mitre=["T1499"],
                            ):
                                count += 1

                            if AUTO_RESPONSE and restarts >= 10:
                                try:
                                    client.patch(
                                        f"{url}/api/v1/namespaces/{ns}/pods/{pod_name}",
                                        headers={**headers, "Content-Type": "application/merge-patch+json"},
                                        content=(
                                            '{"metadata":{"annotations":{'
                                            '"purpleclaw.io/threat":"crash-loop",'
                                            f'"purpleclaw.io/restarts":"{restarts}"'
                                            '}}}'
                                        ),
                                    )
                                except Exception:
                                    pass

                    for container in spec.get("containers", []):
                        sc = container.get("securityContext", {})
                        if sc.get("privileged") or sc.get("allowPrivilegeEscalation"):
                            if _make_finding(
                                db,
                                title=f"K8s privileged container: {ns}/{pod_name}",
                                description=f"Container {container.get('name')} runs privileged=true or allowPrivilegeEscalation=true.",
                                severity=Severity.high, source=f"{source_label}/Auto",
                                evidence=f"ns={ns} pod={pod_name} sc={sc}",
                                remediation="Remove securityContext.privileged and drop capabilities.",
                                mitre=["T1611"],
                            ):
                                count += 1

                    for cs in status.get("initContainerStatuses", []) + status.get("containerStatuses", []):
                        waiting = cs.get("state", {}).get("waiting", {})
                        if waiting.get("reason") in ("ImagePullBackOff", "ErrImagePull"):
                            if _make_finding(
                                db,
                                title=f"K8s image pull failure: {ns}/{pod_name}",
                                description=f"Container {cs.get('name')} cannot pull its image.",
                                severity=Severity.medium, source=f"{source_label}/Auto",
                                evidence=f"ns={ns} pod={pod_name} reason={waiting.get('reason')}",
                                remediation=f"kubectl describe pod -n {ns} {pod_name}",
                            ):
                                count += 1

            # New cluster-admin bindings
            try:
                crb = client.get(f"{url}/apis/rbac.authorization.k8s.io/v1/clusterrolebindings", headers=headers)
                if crb.status_code == 200:
                    now = datetime.utcnow()
                    for binding in crb.json().get("items", []):
                        meta = binding.get("metadata", {})
                        role_ref = binding.get("roleRef", {})
                        if role_ref.get("name") != "cluster-admin":
                            continue
                        try:
                            created = datetime.fromisoformat(
                                meta.get("creationTimestamp", "").replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                            if (now - created).total_seconds() / 3600 > 2:
                                continue
                        except Exception:
                            continue
                        subjects = [s.get("name", "?") for s in binding.get("subjects", [])]
                        if _make_alert(
                            db,
                            title=f"[K8s] New cluster-admin binding: {meta.get('name')}",
                            description=f"ClusterRoleBinding granting cluster-admin created recently. Subjects: {', '.join(subjects)}",
                            severity=AlertSeverity.critical, source=f"{source_label}/Auto",
                            rule_name=f"k8s-cluster-admin:{meta.get('name')}:{url}",
                            raw_data=binding, mitre=["T1078", "T1548"],
                        ):
                            count += 1
            except Exception:
                pass
    except Exception as exc:
        logger.debug("K8s detect failed for %s: %s", url, exc)
    return count


# ── New asset detector ────────────────────────────────────────────────────────

def _detect_new_assets(db: Session) -> int:
    """Flag auto-discovered assets that appeared in the last 30 minutes."""
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    new_assets = (
        db.query(Asset)
        .filter(Asset.created_at >= cutoff, Asset.status == AssetStatus.active)
        .all()
    )
    count = 0
    for asset in new_assets:
        tags = asset.tags or []
        if "auto-discovered" not in tags:
            continue
        if any(t in tags for t in ("loki", "grafana", "ollama", "mlflow")):
            continue
        if _make_finding(
            db,
            title=f"New network asset: {asset.name}",
            description=(
                f"Previously unknown asset discovered: {asset.name} ({asset.type.value}). "
                f"IP: {asset.ip_address}. Services: {asset.services}"
            ),
            severity=Severity.low, source="Discovery/Auto",
            asset_id=asset.id,
            evidence=f"First seen: {asset.created_at}. Tags: {tags}",
            remediation="Verify this asset is known. If unexpected, investigate for unauthorized access.",
            mitre=["T1133", "T1210"],
        ):
            count += 1
    return count


# ── Auto-response ─────────────────────────────────────────────────────────────

def _block_ips(ips: list[str], reason: str) -> None:
    import subprocess
    for ip in ips:
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
            continue
        if ip.startswith(("10.", "172.16.", "172.17.", "192.168.", "127.")):
            continue
        try:
            result = subprocess.run(
                ["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"],
                capture_output=True, timeout=3,
            )
            if result.returncode != 0:
                subprocess.run(
                    ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP",
                     "-m", "comment", "--comment", f"purpleclaw:{reason}"],
                    capture_output=True, timeout=3,
                )
                logger.warning("AUTO-RESPONSE: blocked %s (%s)", ip, reason)
        except Exception as exc:
            logger.debug("iptables block failed %s: %s", ip, exc)


def _auto_escalate(db: Session) -> int:
    alerts = (
        db.query(Alert)
        .filter(
            Alert.severity == AlertSeverity.critical,
            Alert.status == AlertStatus.open,
            Alert.incident_id.is_(None),
        )
        .limit(5)
        .all()
    )
    count = 0
    for alert in alerts:
        incident = Incident(
            title=f"[Auto] {alert.title}",
            description=f"Auto-escalated from critical alert.\n\n{alert.description}",
            severity=IncidentSeverity.critical,
            status=IncidentStatus.new,
            alert_ids=[alert.id],
            attack_vector="automated-detection",
        )
        db.add(incident)
        db.flush()
        alert.incident_id = incident.id
        count += 1
    return count


# ── Engine ────────────────────────────────────────────────────────────────────

class ThreatEngine:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory
        self._timeout = float(os.getenv("THREAT_TIMEOUT", "8"))

    def run(self) -> dict[str, int]:
        results: dict[str, int] = {
            "prometheus": 0, "loki": 0, "kubernetes": 0,
            "new_assets": 0, "incidents": 0,
        }

        # Ensure registry has at least env-configured services
        if not svc_registry.get_all():
            svc_registry.seed_from_env()

        db = self._session_factory()
        try:
            # Run detectors for every discovered Prometheus instance
            for entry in svc_registry.get_by_type("prometheus"):
                if entry.url:
                    results["prometheus"] += _detect_on_prometheus(
                        db, entry.url,
                        f"Prometheus@{entry.host}:{entry.port}",
                        self._timeout,
                    )

            # Run detectors for every discovered Loki instance
            for entry in svc_registry.get_by_type("loki"):
                if entry.url:
                    results["loki"] += _detect_on_loki(
                        db, entry.url,
                        f"Loki@{entry.host}:{entry.port}",
                        self._timeout,
                    )

            # Run detectors for every discovered Kubernetes API
            for entry in svc_registry.get_by_type("kubernetes"):
                if entry.url:
                    results["kubernetes"] += _detect_on_kubernetes(
                        db, entry.url,
                        f"K8s@{entry.host}:{entry.port}",
                        self._timeout,
                    )

            results["new_assets"] = _detect_new_assets(db)
            db.commit()

            results["incidents"] = _auto_escalate(db)
            db.commit()

            total = sum(results.values())
            if total > 0:
                logger.info("Threat scan: %d new findings/alerts/incidents %s", total, results)
        except Exception as exc:
            db.rollback()
            logger.error("Threat engine error: %s", exc)
        finally:
            db.close()

        return results
