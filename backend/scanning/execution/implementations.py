from __future__ import annotations

import logging
import socket
import ssl
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

from datasources.pipeline.models import QuerySpec
from datasources.pipeline.query import query_data
from persistence import list_assets, list_findings, list_inventory, list_telemetry_source_health, list_vulnerability_matches
from scanning.models import ScanPolicy, ScanRequest

logger = logging.getLogger("purpleclaw.scan")

_SECURITY_HEADERS = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]

_WEAK_CIPHERS = {"RC4", "NULL", "DES", "EXPORT", "MD5"}
_WEAK_TLS_VERSIONS = {"TLSv1", "TLSv1.1", "SSLv2", "SSLv3"}
_COMMON_PORTS = {21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns", 80: "http", 110: "pop3", 143: "imap", 443: "https", 445: "smb", 3306: "mysql", 5432: "postgres", 6379: "redis", 8080: "http-alt", 8443: "https-alt", 27017: "mongodb"}


def run_inventory_match(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    matches = list_vulnerability_matches(request.environment_id)
    if asset is not None:
        matches = [f for f in matches if f.asset_id == asset.id]
    return {
        "title": "Inventory vulnerability match review",
        "category": "vulnerability",
        "severity": "high" if matches else "low",
        "score": 82 if matches else 18,
        "evidence_summary": f"CVE inventory comparison returned {len(matches)} match(es): {', '.join(m.title for m in matches[:3]) or 'none'}",
        "details": {"match_count": len(matches), "matches": [m.title for m in matches[:5]]},
    }


def run_tls_check(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    target = request.target
    hostname, port = _parse_host_port(target, default_port=443)

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        with socket.create_connection((hostname, port), timeout=6) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version() or "unknown"

                not_after_raw = cert.get("notAfter", "")
                try:
                    not_after = datetime.strptime(not_after_raw, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (not_after - datetime.now(timezone.utc)).days
                except ValueError:
                    not_after = None
                    days_left = 9999

                issues: list[str] = []
                severity = "low"
                score = 15

                if days_left < 0:
                    issues.append(f"Certificate EXPIRED {abs(days_left)} days ago")
                    severity, score = "critical", 95
                elif days_left < 14:
                    issues.append(f"Certificate expires in {days_left} days — URGENT")
                    severity, score = "high", 85
                elif days_left < 30:
                    issues.append(f"Certificate expires in {days_left} days")
                    if severity not in ("critical", "high"):
                        severity, score = "medium", 60

                if version in _WEAK_TLS_VERSIONS:
                    issues.append(f"Weak TLS version: {version}")
                    if severity not in ("critical",):
                        severity, score = "high", max(score, 80)

                cipher_name = cipher[0] if cipher else "unknown"
                if any(weak in cipher_name.upper() for weak in _WEAK_CIPHERS):
                    issues.append(f"Weak cipher suite: {cipher_name}")
                    if severity not in ("critical",):
                        severity, score = "high", max(score, 75)

                expiry_str = not_after.strftime("%Y-%m-%d") if not_after else "unknown"
                evidence = f"TLS {version} | Cipher: {cipher_name} | Expires: {expiry_str} ({days_left}d left)"
                if issues:
                    evidence += f" | Issues: {'; '.join(issues)}"

                return {
                    "title": "TLS certificate inspection",
                    "category": "tls",
                    "severity": severity,
                    "score": score,
                    "evidence_summary": evidence,
                    "details": {
                        "hostname": hostname,
                        "port": port,
                        "tls_version": version,
                        "cipher": cipher_name,
                        "days_until_expiry": days_left,
                        "expiry_date": expiry_str,
                        "issues": issues,
                        "live_check": True,
                    },
                }

    except ssl.SSLCertVerificationError as exc:
        return {
            "title": "TLS certificate verification failed",
            "category": "tls",
            "severity": "high",
            "score": 85,
            "evidence_summary": f"TLS certificate verification failed for {hostname}:{port} — {exc}",
            "details": {"hostname": hostname, "port": port, "error": str(exc), "live_check": True},
        }

    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        asset = _resolve_asset(request.environment_id, request.target)
        exposure = asset.exposure if asset else "unknown"
        return {
            "title": "TLS endpoint not reachable",
            "category": "tls",
            "severity": "medium" if "internet" in exposure else "info",
            "score": 35 if "internet" in exposure else 8,
            "evidence_summary": f"Host {hostname}:{port} not reachable for TLS check (exposure={exposure}). Reason: {exc}",
            "details": {"hostname": hostname, "port": port, "error": str(exc), "exposure": exposure, "live_check": False},
        }


def run_header_analysis(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    target = request.target
    if "://" not in target:
        urls = [f"https://{target}", f"http://{target}"]
    else:
        urls = [target]

    for url in urls:
        result = _fetch_headers(url)
        if result is not None:
            return result

    parsed = urlparse(f"https://{target}" if "://" not in target else target)
    return {
        "title": "HTTP security header review (host unreachable)",
        "category": "headers",
        "severity": "medium",
        "score": 50,
        "evidence_summary": f"Target {parsed.netloc or parsed.path} was not reachable for live header inspection.",
        "details": {"target": target, "live_check": False},
    }


def run_service_detection(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    hostname, _ = _parse_host_port(request.target, default_port=80)
    open_ports: list[dict[str, object]] = []
    risky: list[str] = []

    scan_ports = list(_COMMON_PORTS.keys())[:12]
    for port in scan_ports:
        if _port_open(hostname, port, timeout=1.5):
            service = _COMMON_PORTS[port]
            open_ports.append({"port": port, "service": service})
            if service in ("telnet", "ftp", "smb", "redis", "mongodb"):
                risky.append(f"{service}/{port}")

    if not open_ports:
        asset = _resolve_asset(request.environment_id, request.target)
        inventory = list_inventory(request.environment_id)
        services = [item.component_name for item in inventory if asset and item.asset_id == asset.id]
        return {
            "title": "Service detection (inventory-based fallback)",
            "category": "service_detection",
            "severity": "low",
            "score": 20,
            "evidence_summary": f"No live ports reachable — inventory lists {len(services)} service(s): {', '.join(services[:6]) or 'none'}",
            "details": {"services": services, "live_check": False},
        }

    severity = "high" if risky else ("medium" if len(open_ports) > 6 else "low")
    score = 80 if risky else (55 if len(open_ports) > 6 else 25)
    evidence = f"Found {len(open_ports)} open port(s): {', '.join(str(p['port']) + '/' + str(p['service']) for p in open_ports[:8])}"
    if risky:
        evidence += f" — RISKY: {', '.join(risky)}"

    return {
        "title": "Live service and port detection",
        "category": "service_detection",
        "severity": severity,
        "score": score,
        "evidence_summary": evidence,
        "details": {"open_ports": open_ports, "risky_services": risky, "live_check": True},
    }


def run_config_audit(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    telemetry_sources = asset.telemetry_sources if asset else []
    findings = list_findings(request.environment_id)
    related = [f for f in findings if asset and f.asset_id == asset.id]

    issues: list[str] = []
    if len(telemetry_sources) < 2:
        issues.append("Insufficient telemetry coverage (fewer than 2 sources)")
    if not asset:
        issues.append("Asset not registered in approved inventory")
    critical_open = [f for f in related if f.severity == "critical" and f.status == "open"]
    if critical_open:
        issues.append(f"{len(critical_open)} critical finding(s) remain open")

    severity = "high" if len(issues) >= 2 else ("medium" if issues else "low")
    score = 75 if len(issues) >= 2 else (50 if issues else 20)

    return {
        "title": "Configuration and coverage audit",
        "category": "misconfiguration",
        "severity": severity,
        "score": score,
        "evidence_summary": f"Audit found {len(issues)} issue(s) across configuration and coverage checks. {'; '.join(issues) or 'No issues found.'}",
        "details": {
            "telemetry_sources": telemetry_sources,
            "related_findings": len(related),
            "critical_open": len(critical_open),
            "issues": issues,
        },
    }


def run_exposure_review(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    exposure = asset.exposure if asset else "unknown"
    hostname, port = _parse_host_port(request.target, default_port=443)
    internet_reachable = False

    if exposure in ("internet-facing", "public"):
        internet_reachable = _port_open(hostname, port, timeout=3)

    severity = "medium" if "internet" in exposure else "low"
    score = 65 if internet_reachable else (40 if "internet" in exposure else 15)
    evidence = f"Asset exposure classification: {exposure}"
    if internet_reachable:
        evidence += f" — confirmed reachable on port {port} from scan host"

    return {
        "title": "Exposure and attack surface review",
        "category": "exposure",
        "severity": severity,
        "score": score,
        "evidence_summary": evidence,
        "details": {
            "exposure": exposure,
            "internet_reachable": internet_reachable,
            "port_checked": port,
            "allowed_network_ranges": policy.allowed_network_ranges,
        },
    }


def run_telemetry_gap_check(request: ScanRequest, policy: ScanPolicy) -> dict[str, object]:
    asset = _resolve_asset(request.environment_id, request.target)
    telemetry_sources = asset.telemetry_sources if asset else []
    coverage = list_telemetry_source_health(request.environment_id)
    degraded = [item for item in coverage if item.status in ("degraded", "unavailable")]

    query_result = query_data(
        request.environment_id,
        QuerySpec(record_types=["metric", "event"], aggregate="count", group_by=["status"], limit=10),
    )

    gaps: list[str] = []
    if len(telemetry_sources) < 2:
        gaps.append(f"Only {len(telemetry_sources)} telemetry source(s) mapped (minimum 2 recommended)")
    if degraded:
        gaps.append(f"{len(degraded)} source(s) degraded or unavailable: {', '.join(item.source_name for item in degraded[:3])}")

    severity = "high" if len(gaps) >= 2 else ("medium" if gaps else "low")
    score = 85 if len(gaps) >= 2 else (55 if gaps else 20)

    return {
        "title": "Telemetry coverage gap analysis",
        "category": "monitoring_gap",
        "severity": severity,
        "score": score,
        "evidence_summary": f"Coverage mapped {len(telemetry_sources)} source(s), {len(degraded)} degraded. Gaps: {'; '.join(gaps) or 'none'}",
        "details": {
            "telemetry_sources": telemetry_sources,
            "degraded_sources": [item.source_name for item in degraded],
            "gaps": gaps,
            "pipeline_aggregates": query_result.get("aggregates", []),
        },
    }


def _resolve_asset(environment_id: str, target: str):
    return next((a for a in list_assets(environment_id) if target in {a.id, a.name}), None)


def _parse_host_port(target: str, default_port: int) -> tuple[str, int]:
    if "://" in target:
        parsed = urlparse(target)
        hostname = parsed.hostname or target
        port = parsed.port or default_port
    elif ":" in target:
        parts = target.rsplit(":", 1)
        hostname = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            port = default_port
    else:
        hostname = target
        port = default_port
    return hostname, port


def _port_open(hostname: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((hostname, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def _fetch_headers(url: str) -> dict[str, object] | None:
    try:
        import httpx
        response = httpx.get(url, timeout=6, follow_redirects=True, verify=False)
        headers = {k.lower(): v for k, v in response.headers.items()}

        missing = [h for h in _SECURITY_HEADERS if h not in headers]
        present = [h for h in _SECURITY_HEADERS if h in headers]

        severity = "critical" if len(missing) >= 5 else ("high" if len(missing) >= 3 else ("medium" if missing else "low"))
        score = min(15 + len(missing) * 14, 95)

        info_leak: list[str] = []
        if "server" in headers and headers["server"] not in ("", "nginx", "apache"):
            info_leak.append(f"Server: {headers['server']}")
        if "x-powered-by" in headers:
            info_leak.append(f"X-Powered-By: {headers['x-powered-by']}")

        evidence = f"[{url}] {len(present)}/{len(_SECURITY_HEADERS)} security headers present"
        if missing:
            evidence += f" — missing: {', '.join(missing[:3])}"
        if info_leak:
            evidence += f" — info disclosure: {', '.join(info_leak)}"

        return {
            "title": "HTTP security header analysis",
            "category": "headers",
            "severity": severity,
            "score": score,
            "evidence_summary": evidence,
            "details": {
                "url": url,
                "status_code": response.status_code,
                "headers_present": present,
                "headers_missing": missing,
                "information_disclosure": info_leak,
                "server": headers.get("server", "not disclosed"),
                "live_check": True,
            },
        }
    except Exception:
        return None
