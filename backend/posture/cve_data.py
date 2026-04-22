from __future__ import annotations

from dataclasses import dataclass

from posture.models import FindingSeverity


@dataclass(frozen=True)
class CveRecord:
    """Seeded defensive CVE matching metadata."""

    cve_id: str
    component_name: str
    vulnerable_versions: list[str]
    severity: FindingSeverity
    title: str
    description: str
    recommendation: str
    affected_component: str


SEEDED_CVES: tuple[CveRecord, ...] = (
    CveRecord(
        cve_id="CVE-2023-44487",
        component_name="nginx",
        vulnerable_versions=["1.24.0", "1.23.4"],
        severity=FindingSeverity.HIGH,
        title="HTTP/2 rapid reset exposure in nginx",
        description="The detected nginx version should be reviewed for HTTP/2 rapid reset exposure and vendor fixes.",
        recommendation="Upgrade nginx to a vendor-fixed build and confirm HTTP/2 rate limiting controls.",
        affected_component="nginx HTTP/2 service",
    ),
    CveRecord(
        cve_id="CVE-2023-38408",
        component_name="openssh",
        vulnerable_versions=["8.9p1", "9.0p1", "9.1p1", "9.2p1", "9.3p1"],
        severity=FindingSeverity.HIGH,
        title="OpenSSH agent forwarding library load risk",
        description="The detected OpenSSH version is in the seeded affected range for agent forwarding risk review.",
        recommendation="Upgrade OpenSSH and disable agent forwarding where it is not explicitly required.",
        affected_component="OpenSSH service",
    ),
    CveRecord(
        cve_id="CVE-2023-3128",
        component_name="grafana",
        vulnerable_versions=["9.5.2", "9.5.1", "9.4.7"],
        severity=FindingSeverity.MEDIUM,
        title="Grafana access control bypass review",
        description="The detected Grafana version matches a seeded access control vulnerability record.",
        recommendation="Upgrade Grafana to a fixed release and review dashboard permission boundaries.",
        affected_component="Grafana web application",
    ),
    CveRecord(
        cve_id="CVE-2023-29406",
        component_name="prometheus",
        vulnerable_versions=["2.43.0", "2.44.0"],
        severity=FindingSeverity.MEDIUM,
        title="Prometheus UI denial-of-service exposure",
        description="The detected Prometheus version matches a seeded UI availability vulnerability record.",
        recommendation="Upgrade Prometheus and restrict administrative UI access to trusted networks.",
        affected_component="Prometheus server",
    ),
    CveRecord(
        cve_id="CVE-2023-25153",
        component_name="containerd",
        vulnerable_versions=["1.6.15", "1.6.16", "1.6.17"],
        severity=FindingSeverity.HIGH,
        title="containerd image import permission risk",
        description="The detected containerd version matches a seeded container runtime vulnerability record.",
        recommendation="Upgrade containerd and verify runtime hardening and image admission controls.",
        affected_component="containerd runtime",
    ),
    CveRecord(
        cve_id="CVE-2023-2727",
        component_name="kubelet",
        vulnerable_versions=["1.26.3", "1.25.8", "1.24.12"],
        severity=FindingSeverity.HIGH,
        title="Kubelet service account token review",
        description="The detected kubelet version matches a seeded Kubernetes node vulnerability record.",
        recommendation="Upgrade kubelet and verify node authorization and service account token controls.",
        affected_component="kubelet node agent",
    ),
    CveRecord(
        cve_id="CVE-2022-21698",
        component_name="node-exporter",
        vulnerable_versions=["1.3.1", "1.4.0"],
        severity=FindingSeverity.LOW,
        title="node-exporter metrics exposure review",
        description="The detected node-exporter version matches a seeded monitoring exposure review item.",
        recommendation="Upgrade node-exporter and ensure metrics endpoints are restricted to monitoring networks.",
        affected_component="node-exporter metrics endpoint",
    ),
)
