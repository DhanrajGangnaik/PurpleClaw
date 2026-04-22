from collectors.loki import get_environment_log_metrics
from collectors.prometheus import get_environment_metrics
from executor.models import ExecutionResult
from planner.schemas import ExercisePlan, utc_now
from posture.models import (
    Alert,
    Asset,
    AutomationRun,
    DataSource,
    DependencyStatus,
    Environment,
    Finding,
    FindingSeverity,
    FindingSeverityCount,
    IncidentSummary,
    InventoryRecord,
    Policy,
    Report,
    RemediationTask,
    RiskByAsset,
    SecuritySignal,
    ServiceHealth,
    SystemMode,
    SystemModeName,
    TelemetrySourceHealth,
    TelemetrySummary,
)
from posture.cve_matcher import match_inventory_to_cves
from posture.scoring import calculate_asset_risk, calculate_finding_score, rank_findings
from persistence.database import db


PRIMARY_ENVIRONMENT_ID = "homelab"
_ENVIRONMENTS: dict[str, Environment] = {
    "homelab": Environment(
        environment_id="homelab",
        name="Homelab",
        type="homelab",
        description="Primary home lab environment for safe posture validation.",
        status="active",
    ),
    "lab": Environment(
        environment_id="lab",
        name="Lab",
        type="lab",
        description="Controlled lab environment for repeatable validation work.",
        status="active",
    ),
    "staging": Environment(
        environment_id="staging",
        name="Staging",
        type="staging",
        description="Production-like staging environment for pre-release posture review.",
        status="active",
    ),
}
_PLANS: dict[str, dict[str, ExercisePlan]] = {environment_id: {} for environment_id in _ENVIRONMENTS}
_EXECUTION_RESULTS: list[ExecutionResult] = []
_SYSTEM_MODE = SystemMode(mode=SystemModeName.DEMO, last_tracking_run_at=None, tracking_enabled=False)
_AUTOMATION_RUNS: list[AutomationRun] = []
_DEMO_ASSETS: dict[str, Asset] = {
    "asset-001": Asset(
        id="asset-001",
        environment_id="homelab",
        name="edge-gateway-01",
        asset_type="network",
        environment="homelab",
        owner="platform",
        exposure="internet-adjacent",
        criticality="critical",
        risk_score=92,
        status="needs-attention",
        tags=["gateway", "network", "remote-access"],
        telemetry_sources=["firewall", "zeek", "dns"],
    ),
    "asset-002": Asset(
        id="asset-002",
        environment_id="lab",
        name="k8s-control-01",
        asset_type="kubernetes",
        environment="cluster",
        owner="platform",
        exposure="internal",
        criticality="critical",
        risk_score=84,
        status="review",
        tags=["kubernetes", "control-plane"],
        telemetry_sources=["audit", "falco", "prometheus"],
    ),
    "asset-003": Asset(
        id="asset-003",
        environment_id="homelab",
        name="nas-vault-01",
        asset_type="storage",
        environment="homelab",
        owner="storage",
        exposure="internal",
        criticality="high",
        risk_score=71,
        status="review",
        tags=["storage", "backup"],
        telemetry_sources=["syslog", "file-integrity"],
    ),
    "asset-004": Asset(
        id="asset-004",
        environment_id="staging",
        name="media-node-02",
        asset_type="server",
        environment="services",
        owner="apps",
        exposure="internal",
        criticality="medium",
        risk_score=45,
        status="monitored",
        tags=["linux", "containers"],
        telemetry_sources=["osquery", "container-runtime"],
    ),
    "asset-005": Asset(
        id="asset-005",
        environment_id="homelab",
        name="identity-core-01",
        asset_type="identity",
        environment="homelab",
        owner="security",
        exposure="internal",
        criticality="critical",
        risk_score=88,
        status="needs-attention",
        tags=["identity", "sso", "mfa"],
        telemetry_sources=["auth", "audit", "edr"],
    ),
    "asset-006": Asset(
        id="asset-006",
        environment_id="lab",
        name="observability-01",
        asset_type="monitoring",
        environment="ops",
        owner="security",
        exposure="internal",
        criticality="high",
        risk_score=39,
        status="healthy",
        tags=["logging", "metrics", "siem"],
        telemetry_sources=["loki", "prometheus", "alertmanager"],
    ),
}
_TRACKING_ASSETS: dict[str, Asset] = {}
_DEMO_INVENTORY: dict[str, InventoryRecord] = {
    "inv-001": InventoryRecord(inventory_id="inv-001", environment_id="homelab", asset_id="asset-001", component_name="nginx", component_type="service", version="1.24.0"),
    "inv-002": InventoryRecord(inventory_id="inv-002", environment_id="homelab", asset_id="asset-001", component_name="openssh", component_type="service", version="9.3p1"),
    "inv-003": InventoryRecord(inventory_id="inv-003", asset_id="asset-002", environment_id="lab", component_name="containerd", component_type="package", version="1.6.17"),
    "inv-004": InventoryRecord(inventory_id="inv-004", environment_id="lab", asset_id="asset-002", component_name="kubelet", component_type="binary", version="1.26.3"),
    "inv-005": InventoryRecord(inventory_id="inv-005", environment_id="lab", asset_id="asset-006", component_name="grafana", component_type="service", version="9.5.2"),
    "inv-006": InventoryRecord(inventory_id="inv-006", environment_id="lab", asset_id="asset-006", component_name="prometheus", component_type="service", version="2.44.0"),
    "inv-007": InventoryRecord(inventory_id="inv-007", environment_id="lab", asset_id="asset-006", component_name="node-exporter", component_type="binary", version="1.4.0"),
    "inv-008": InventoryRecord(inventory_id="inv-008", environment_id="staging", asset_id="asset-004", component_name="containerd", component_type="package", version="1.6.20"),
    "inv-009": InventoryRecord(inventory_id="inv-009", environment_id="homelab", asset_id="asset-005", component_name="openssh", component_type="service", version="9.6p1"),
    "inv-010": InventoryRecord(inventory_id="inv-010", environment_id="homelab", asset_id="asset-003", component_name="node-exporter", component_type="binary", version="1.6.1"),
}
_TRACKING_INVENTORY: dict[str, InventoryRecord] = {}
_DEMO_FINDINGS: dict[str, Finding] = {
    "finding-001": Finding(
        id="finding-001",
        environment_id="homelab",
        asset_id="asset-001",
        title="Remote administration exposure requires tighter policy",
        severity=FindingSeverity.CRITICAL,
        category="exposure",
        status="open",
        exposure="internet-adjacent management path",
        evidence_summary="Gateway telemetry shows management service reachability from untrusted networks.",
        verification="Confirm allowlist-only access and alert on policy drift.",
        score=100,
        confidence="high",
        affected_component="remote administration service",
    ),
    "finding-002": Finding(
        id="finding-002",
        environment_id="homelab",
        asset_id="asset-001",
        title="Firewall deny events lack ownership tags",
        severity=FindingSeverity.MEDIUM,
        category="monitoring_gap",
        status="open",
        exposure="triage delay",
        evidence_summary="Network events are collected but missing service owner enrichment.",
        verification="Sample denied events include owner and asset labels.",
        score=64,
        confidence="medium",
        affected_component="firewall event enrichment",
    ),
    "finding-003": Finding(
        id="finding-003",
        environment_id="lab",
        asset_id="asset-002",
        title="Kubernetes audit retention below policy",
        severity=FindingSeverity.HIGH,
        category="misconfiguration",
        status="in-progress",
        exposure="reduced investigation window",
        evidence_summary="Audit logs retain seven days while the policy target is thirty days.",
        verification="Validate thirty days of audit events are searchable.",
        score=77,
        confidence="high",
        affected_component="kubernetes audit logging",
    ),
    "finding-004": Finding(
        id="finding-004",
        environment_id="lab",
        asset_id="asset-002",
        title="Privileged workload review overdue",
        severity=FindingSeverity.HIGH,
        category="runtime_risk",
        status="open",
        exposure="control-plane hardening gap",
        evidence_summary="Two privileged workloads have not been reviewed this quarter.",
        verification="Document approvals and expected runtime constraints.",
        score=82,
        confidence="medium",
        affected_component="privileged workload policy",
    ),
    "finding-005": Finding(
        id="finding-005",
        environment_id="homelab",
        asset_id="asset-003",
        title="Backup verification cadence is inconsistent",
        severity=FindingSeverity.HIGH,
        category="misconfiguration",
        status="open",
        exposure="recovery uncertainty",
        evidence_summary="Recent backups exist, but restore verification results are incomplete.",
        verification="Complete restore validation and capture checksum evidence.",
        score=70,
        confidence="medium",
        affected_component="backup validation process",
    ),
    "finding-006": Finding(
        id="finding-006",
        environment_id="homelab",
        asset_id="asset-003",
        title="Storage firmware inventory is stale",
        severity=FindingSeverity.MEDIUM,
        category="vulnerability",
        status="open",
        exposure="patch visibility gap",
        evidence_summary="Firmware metadata has not refreshed in more than fourteen days.",
        verification="Refresh inventory and compare against approved baseline.",
        score=45,
        confidence="medium",
        affected_component="storage firmware inventory",
    ),
    "finding-007": Finding(
        id="finding-007",
        environment_id="staging",
        asset_id="asset-004",
        title="Container image provenance missing for service workload",
        severity=FindingSeverity.MEDIUM,
        category="vulnerability",
        status="open",
        exposure="unverified package lineage",
        evidence_summary="One service image lacks signed provenance metadata.",
        verification="Attach provenance attestation and verify during deployment.",
        score=45,
        confidence="medium",
        affected_component="container image provenance",
    ),
    "finding-008": Finding(
        id="finding-008",
        environment_id="staging",
        asset_id="asset-004",
        title="Runtime detection rule needs validation",
        severity=FindingSeverity.LOW,
        category="runtime_risk",
        status="in-progress",
        exposure="detection confidence gap",
        evidence_summary="The expected container drift alert has not been verified this month.",
        verification="Run safe validation plan and record expected telemetry.",
        score=25,
        confidence="low",
        affected_component="container drift detection",
    ),
    "finding-009": Finding(
        id="finding-009",
        environment_id="homelab",
        asset_id="asset-005",
        title="MFA enforcement exception requires review",
        severity=FindingSeverity.CRITICAL,
        category="misconfiguration",
        status="open",
        exposure="identity assurance gap",
        evidence_summary="One service account remains outside the current MFA enforcement policy.",
        verification="Remove exception or document compensating controls.",
        score=97,
        confidence="high",
        affected_component="MFA enforcement policy",
    ),
    "finding-010": Finding(
        id="finding-010",
        environment_id="homelab",
        asset_id="asset-005",
        title="Authentication alert routing is incomplete",
        severity=FindingSeverity.HIGH,
        category="monitoring_gap",
        status="open",
        exposure="delayed identity response",
        evidence_summary="High-risk authentication alerts do not page the security owner.",
        verification="Trigger safe alert test and confirm route delivery.",
        score=83,
        confidence="high",
        affected_component="authentication alert routing",
    ),
    "finding-011": Finding(
        id="finding-011",
        environment_id="lab",
        asset_id="asset-006",
        title="SIEM parser coverage missing one source",
        severity=FindingSeverity.MEDIUM,
        category="monitoring_gap",
        status="open",
        exposure="partial detection context",
        evidence_summary="One syslog source is ingested as raw text without parsed fields.",
        verification="Parser extracts host, service, severity, and event action fields.",
        score=51,
        confidence="medium",
        affected_component="SIEM parser coverage",
    ),
    "finding-012": Finding(
        id="finding-012",
        environment_id="lab",
        asset_id="asset-006",
        title="Alert fatigue threshold needs tuning",
        severity=FindingSeverity.LOW,
        category="monitoring_gap",
        status="accepted",
        exposure="triage noise",
        evidence_summary="Low priority alert volume increased after onboarding a new service.",
        verification="Tune grouping rules while preserving critical notification paths.",
        score=26,
        confidence="low",
        affected_component="alert grouping threshold",
    ),
}
_TRACKING_FINDINGS: dict[str, Finding] = {}
_DEMO_REMEDIATIONS: dict[str, RemediationTask] = {
    "rem-001": RemediationTask(
        id="rem-001",
        environment_id="homelab",
        finding_id="finding-001",
        title="Restrict remote administration to approved management networks",
        status="in-progress",
        owner="platform",
        due_date=utc_now(),
        steps=["Review allowed source ranges", "Apply gateway policy update", "Verify deny telemetry"],
        verification="Management path is reachable only from approved networks.",
    ),
    "rem-002": RemediationTask(
        id="rem-002",
        environment_id="lab",
        finding_id="finding-003",
        title="Extend Kubernetes audit retention",
        status="open",
        owner="platform",
        due_date=utc_now(),
        steps=["Increase log retention", "Backfill dashboard panel", "Validate search over policy window"],
        verification="Audit search returns events across the full retention target.",
    ),
    "rem-003": RemediationTask(
        id="rem-003",
        environment_id="lab",
        finding_id="finding-004",
        title="Review privileged workload approvals",
        status="open",
        owner="security",
        due_date=utc_now(),
        steps=["List privileged workloads", "Confirm business owner", "Record runtime constraints"],
        verification="Every privileged workload has a current approval record.",
    ),
    "rem-004": RemediationTask(
        id="rem-004",
        environment_id="homelab",
        finding_id="finding-005",
        title="Complete backup restore verification",
        status="in-progress",
        owner="storage",
        due_date=utc_now(),
        steps=["Select restore sample", "Restore to isolated validation target", "Record checksum results"],
        verification="Restore validation evidence is attached to the backup report.",
    ),
    "rem-005": RemediationTask(
        id="rem-005",
        environment_id="staging",
        finding_id="finding-007",
        title="Require image provenance checks",
        status="open",
        owner="apps",
        due_date=utc_now(),
        steps=["Enable provenance metadata", "Add deployment verification", "Document exception process"],
        verification="Deployment gate blocks images without approved provenance.",
    ),
    "rem-006": RemediationTask(
        id="rem-006",
        environment_id="homelab",
        finding_id="finding-009",
        title="Remove stale MFA exception",
        status="blocked",
        owner="security",
        due_date=utc_now(),
        steps=["Confirm service owner", "Identify compensating control", "Close or approve exception"],
        verification="Identity policy shows no undocumented MFA exception.",
    ),
    "rem-007": RemediationTask(
        id="rem-007",
        environment_id="homelab",
        finding_id="finding-010",
        title="Route high-risk authentication alerts",
        status="completed",
        owner="security",
        due_date=utc_now(),
        steps=["Update alert route", "Test notification path", "Capture verification timestamp"],
        verification="High-risk authentication alert reaches the security owner channel.",
    ),
    "rem-008": RemediationTask(
        id="rem-008",
        environment_id="lab",
        finding_id="finding-011",
        title="Add parser coverage for raw syslog source",
        status="open",
        owner="security",
        due_date=utc_now(),
        steps=["Map source fields", "Deploy parser", "Validate normalized events"],
        verification="Normalized event fields are present in telemetry summaries.",
    ),
}
_TRACKING_REMEDIATIONS: dict[str, RemediationTask] = {}
_DEMO_POLICIES: dict[str, Policy] = {
    "policy-001": Policy(
        id="policy-001",
        name="Remote Access Exposure Control",
        domain="exposure",
        status="active",
        coverage=82,
        requirements=["Allowlist management access", "Log denied access", "Review exceptions monthly"],
    ),
    "policy-002": Policy(
        id="policy-002",
        name="Telemetry Retention and Parsing",
        domain="telemetry",
        status="active",
        coverage=76,
        requirements=["Retain critical audit logs", "Normalize key fields", "Monitor freshness"],
    ),
    "policy-003": Policy(
        id="policy-003",
        name="Identity Assurance Baseline",
        domain="identity",
        status="review",
        coverage=68,
        requirements=["Enforce MFA", "Review service accounts", "Route high-risk alerts"],
    ),
}
_DEMO_REPORTS: dict[str, Report] = {
    "report-001": Report(
        id="report-001",
        title="Homelab Posture Weekly",
        report_type="posture",
        period="2026-W16",
        summary="Critical exposure and identity exceptions remain the highest priority posture items.",
        key_metrics={"assets": 6, "open_findings": 10, "critical_findings": 2, "completed_remediations": 1},
    ),
    "report-002": Report(
        id="report-002",
        title="Telemetry Coverage Review",
        report_type="telemetry",
        period="April 2026",
        summary="Runtime and network telemetry are strong; parser coverage needs one remediation task.",
        key_metrics={"runtime_coverage": 91, "network_coverage": 86, "infrastructure_coverage": 78},
    ),
}
_DEMO_TELEMETRY_SUMMARIES: dict[str, TelemetrySummary] = {
    "telemetry-runtime": TelemetrySummary(
        id="telemetry-runtime",
        environment_id="homelab",
        source_name="Demo runtime telemetry",
        source_type="runtime",
        source=DataSource.DEMO,
        asset_count=2,
        event_count=18420,
        health_status="healthy",
        notes=["Demo container drift validation ready", "Demo process telemetry mapped to assets"],
    ),
    "telemetry-network": TelemetrySummary(
        id="telemetry-network",
        environment_id="lab",
        source_name="Demo network telemetry",
        source_type="network",
        source=DataSource.DEMO,
        asset_count=2,
        event_count=32680,
        health_status="review",
        notes=["Demo gateway deny events collected", "Demo owner enrichment pending for one feed"],
    ),
    "telemetry-infrastructure": TelemetrySummary(
        id="telemetry-infrastructure",
        environment_id="staging",
        source_name="Demo infrastructure telemetry",
        source_type="infrastructure",
        source=DataSource.DEMO,
        asset_count=2,
        event_count=12990,
        health_status="needs-attention",
        notes=["Demo audit retention below target", "Demo syslog parser requires normalization"],
    ),
}
_DEMO_ALERTS: dict[str, Alert] = {
    "alert-001": Alert(
        alert_id="alert-001",
        environment_id="homelab",
        source="Prometheus",
        title="Gateway packet drop rate elevated",
        severity=FindingSeverity.HIGH,
        status="active",
        asset_id="asset-001",
    ),
    "alert-002": Alert(
        alert_id="alert-002",
        environment_id="homelab",
        source="Loki",
        title="Authentication failures above baseline",
        severity=FindingSeverity.HIGH,
        status="active",
        asset_id="asset-005",
    ),
    "alert-003": Alert(
        alert_id="alert-003",
        environment_id="lab",
        source="Prometheus",
        title="Kubernetes API latency degraded",
        severity=FindingSeverity.MEDIUM,
        status="active",
        asset_id="asset-002",
    ),
    "alert-004": Alert(
        alert_id="alert-004",
        environment_id="staging",
        source="Loki",
        title="Container runtime warning volume increased",
        severity=FindingSeverity.LOW,
        status="triaged",
        asset_id="asset-004",
    ),
}
_DEMO_SECURITY_SIGNALS: dict[str, SecuritySignal] = {
    "signal-001": SecuritySignal(
        signal_id="signal-001",
        environment_id="homelab",
        source="Loki",
        category="authentication",
        title="Repeated failed authentication events",
        severity=FindingSeverity.HIGH,
        confidence="high",
        asset_id="asset-005",
        evidence="Multiple failed login events were observed for identity services during the review window.",
        status="new",
    ),
    "signal-002": SecuritySignal(
        signal_id="signal-002",
        environment_id="homelab",
        source="Firewall",
        category="network_security",
        title="Denied management access from untrusted segment",
        severity=FindingSeverity.CRITICAL,
        confidence="medium",
        asset_id="asset-001",
        evidence="Firewall events show denied management-path traffic from a non-management network.",
        status="investigating",
    ),
    "signal-003": SecuritySignal(
        signal_id="signal-003",
        environment_id="lab",
        source="Kubernetes audit",
        category="runtime",
        title="Privileged workload launch requires review",
        severity=FindingSeverity.HIGH,
        confidence="medium",
        asset_id="asset-002",
        evidence="Audit records include privileged workload settings outside the latest review window.",
        status="new",
    ),
    "signal-004": SecuritySignal(
        signal_id="signal-004",
        environment_id="staging",
        source="Container runtime",
        category="service_error",
        title="Service error burst observed after deploy",
        severity=FindingSeverity.MEDIUM,
        confidence="medium",
        asset_id="asset-004",
        evidence="Application logs show a short-lived increase in service errors after deployment.",
        status="triaged",
    ),
}
_DEMO_INCIDENTS: dict[str, IncidentSummary] = {
    "incident-001": IncidentSummary(
        incident_id="incident-001",
        environment_id="homelab",
        title="Identity signal review",
        severity=FindingSeverity.HIGH,
        status="open",
        related_signal_ids=["signal-001", "signal-002"],
    ),
    "incident-002": IncidentSummary(
        incident_id="incident-002",
        environment_id="lab",
        title="Control plane runtime review",
        severity=FindingSeverity.HIGH,
        status="open",
        related_signal_ids=["signal-003"],
    ),
    "incident-003": IncidentSummary(
        incident_id="incident-003",
        environment_id="staging",
        title="Post-deploy service health review",
        severity=FindingSeverity.MEDIUM,
        status="triaged",
        related_signal_ids=["signal-004"],
    ),
}
_DEMO_SERVICE_HEALTH: dict[str, ServiceHealth] = {
    "service-001": ServiceHealth(service_id="service-001", environment_id="homelab", name="Edge gateway", status="degraded", availability=98, latency_ms=42, error_rate=1.8),
    "service-002": ServiceHealth(service_id="service-002", environment_id="homelab", name="Identity core", status="healthy", availability=100, latency_ms=24, error_rate=0.2),
    "service-003": ServiceHealth(service_id="service-003", environment_id="lab", name="Kubernetes API", status="degraded", availability=97, latency_ms=185, error_rate=2.4),
    "service-004": ServiceHealth(service_id="service-004", environment_id="lab", name="Observability stack", status="healthy", availability=99, latency_ms=58, error_rate=0.4),
    "service-005": ServiceHealth(service_id="service-005", environment_id="staging", name="Media service", status="healthy", availability=99, latency_ms=76, error_rate=0.6),
}
_DEMO_DEPENDENCIES: dict[str, DependencyStatus] = {
    "dep-001": DependencyStatus(dependency_id="dep-001", environment_id="homelab", name="Prometheus", type="metrics", status="healthy", notes="Read-only metrics endpoint configured for posture and NOC summaries."),
    "dep-002": DependencyStatus(dependency_id="dep-002", environment_id="homelab", name="Loki", type="logs", status="degraded", notes="Log coverage requires review for expected authentication and syslog sources."),
    "dep-003": DependencyStatus(dependency_id="dep-003", environment_id="lab", name="Kubernetes API", type="platform", status="degraded", notes="Latency is above the normal operating band."),
    "dep-004": DependencyStatus(dependency_id="dep-004", environment_id="staging", name="Container registry", type="artifact", status="healthy", notes="Image metadata and provenance checks are available."),
}
_DEMO_TELEMETRY_SOURCE_HEALTH: dict[str, TelemetrySourceHealth] = {
    "source-001": TelemetrySourceHealth(source_id="source-001", environment_id="homelab", source_name="Prometheus", source_type="metrics", status="healthy", last_success_at=utc_now(), notes="Target and node summaries are available."),
    "source-002": TelemetrySourceHealth(source_id="source-002", environment_id="homelab", source_name="Loki", source_type="logs", status="degraded", last_success_at=utc_now(), notes="Expected log source coverage is incomplete."),
    "source-003": TelemetrySourceHealth(source_id="source-003", environment_id="lab", source_name="Kubernetes audit", source_type="audit", status="degraded", last_success_at=utc_now(), notes="Retention is below policy target."),
    "source-004": TelemetrySourceHealth(source_id="source-004", environment_id="lab", source_name="Prometheus", source_type="metrics", status="healthy", last_success_at=utc_now(), notes="Control plane and observability metrics are available."),
    "source-005": TelemetrySourceHealth(source_id="source-005", environment_id="staging", source_name="Container runtime", source_type="runtime", status="healthy", last_success_at=utc_now(), notes="Runtime health and warning signals are available."),
}
_TRACKING_TELEMETRY_SUMMARIES: dict[str, TelemetrySummary] = {}
_TRACKING_ALERTS: dict[str, Alert] = {}
_TRACKING_SECURITY_SIGNALS: dict[str, SecuritySignal] = {}
_TRACKING_INCIDENTS: dict[str, IncidentSummary] = {}
_TRACKING_SERVICE_HEALTH: dict[str, ServiceHealth] = {}
_TRACKING_DEPENDENCIES: dict[str, DependencyStatus] = {}
_TRACKING_TELEMETRY_SOURCE_HEALTH: dict[str, TelemetrySourceHealth] = {}
_PROMETHEUS_FINDING_PREFIX = "prometheus"
_LOKI_FINDING_PREFIX = "loki"
_CVE_FINDING_PREFIX = "cve"


def initialize_persistence() -> dict[str, object]:
    """Initialize optional PostgreSQL persistence and seed stable environments."""

    db.init_schema()
    if db.enabled:
        db.upsert_many("environments", _ENVIRONMENTS.values())
    return db.status()


def primary_environment_id() -> str:
    """Return the default environment used when no filter is provided."""

    return PRIMARY_ENVIRONMENT_ID


def normalize_environment_id(environment_id: str | None = None) -> str:
    """Return a known environment ID, defaulting to the primary environment."""

    if environment_id in _ENVIRONMENTS:
        return str(environment_id)
    return PRIMARY_ENVIRONMENT_ID


def list_environments() -> list[Environment]:
    """Return all configured environments."""

    return list(_ENVIRONMENTS.values())


def get_environment(environment_id: str) -> Environment | None:
    """Return one environment by ID, if configured."""

    return _ENVIRONMENTS.get(environment_id)


def get_prometheus_metrics(environment_id: str | None = None) -> dict[str, object]:
    """Return read-only Prometheus metrics for a known environment."""

    return get_environment_metrics(normalize_environment_id(environment_id))


def get_loki_metrics(environment_id: str | None = None) -> dict[str, object]:
    """Return read-only Loki log metrics for a known environment."""

    return get_environment_log_metrics(normalize_environment_id(environment_id))


def save_plan(plan: ExercisePlan, environment_id: str | None = None) -> None:
    """Store or replace an exercise plan by ID."""

    active_environment_id = normalize_environment_id(environment_id)
    environment_plans = _PLANS.setdefault(active_environment_id, {})
    existing = environment_plans.get(plan.id)
    environment_plans[plan.id] = plan.model_copy(
        update={
            "created_at": existing.created_at if existing else plan.created_at,
            "updated_at": utc_now(),
        }
    )


def get_plan(plan_id: str, environment_id: str | None = None) -> ExercisePlan | None:
    """Return a stored exercise plan by ID, if present."""

    return _PLANS.get(normalize_environment_id(environment_id), {}).get(plan_id)


def list_plans(environment_id: str | None = None) -> list[ExercisePlan]:
    """Return all stored exercise plans."""

    return list(_PLANS.get(normalize_environment_id(environment_id), {}).values())


def save_execution_result(result: ExecutionResult, environment_id: str | None = None) -> None:
    """Store an execution result in insertion order."""

    _EXECUTION_RESULTS.append(result.model_copy(update={"environment_id": normalize_environment_id(environment_id)}))


def list_execution_results(environment_id: str | None = None) -> list[ExecutionResult]:
    """Return all stored execution results."""

    active_environment_id = normalize_environment_id(environment_id)
    return [result for result in _EXECUTION_RESULTS if result.environment_id == active_environment_id]


def list_assets(environment_id: str | None = None) -> list[Asset]:
    """Return assets for the active mode."""

    active_environment_id = normalize_environment_id(environment_id)
    return [asset for asset in _active_assets().values() if asset.environment_id == active_environment_id]


def save_inventory_record(record: InventoryRecord, environment_id: str | None = None) -> InventoryRecord:
    """Store an approved inventory record in tracking mode."""

    active_environment_id = normalize_environment_id(environment_id or record.environment_id)
    tracking_record = record.model_copy(update={"environment_id": active_environment_id, "source": DataSource.TRACKING, "detected_at": utc_now()})
    _TRACKING_INVENTORY[tracking_record.inventory_id] = tracking_record
    return tracking_record


def list_inventory(environment_id: str | None = None) -> list[InventoryRecord]:
    """Return component inventory for one environment."""

    return list_inventory_by_environment(environment_id)


def list_inventory_by_environment(environment_id: str | None = None) -> list[InventoryRecord]:
    """Return component inventory for one environment."""

    active_environment_id = normalize_environment_id(environment_id)
    return [record for record in _active_inventory().values() if record.environment_id == active_environment_id]


def list_inventory_by_asset(asset_id: str, environment_id: str | None = None) -> list[InventoryRecord]:
    """Return component inventory for one asset."""

    active_environment_id = normalize_environment_id(environment_id)
    return [record for record in _active_inventory().values() if record.asset_id == asset_id and record.environment_id == active_environment_id]


def list_vulnerability_matches(environment_id: str | None = None) -> list[Finding]:
    """Return seeded CVE matches for the selected environment inventory."""

    active_environment_id = normalize_environment_id(environment_id)
    assets = {asset.id: asset for asset in list_assets(active_environment_id)}
    return rank_findings(match_inventory_to_cves(list_inventory(active_environment_id), assets))


def list_findings(environment_id: str | None = None) -> list[Finding]:
    """Return posture findings for the active mode."""

    active_environment_id = normalize_environment_id(environment_id)
    return [_with_current_score(finding) for finding in _active_findings().values() if finding.environment_id == active_environment_id]


def list_findings_for_asset(asset_id: str, environment_id: str | None = None) -> list[Finding]:
    """Return findings for a specific asset."""

    active_environment_id = normalize_environment_id(environment_id)
    return [_with_current_score(finding) for finding in _active_findings().values() if finding.asset_id == asset_id and finding.environment_id == active_environment_id]


def list_prioritized_findings(environment_id: str | None = None) -> list[Finding]:
    """Return findings sorted by deterministic risk score."""

    return rank_findings(list_findings(environment_id))


def list_remediations(environment_id: str | None = None) -> list[RemediationTask]:
    """Return remediation tasks for the active mode."""

    active_environment_id = normalize_environment_id(environment_id)
    return [task for task in _active_remediations().values() if task.environment_id == active_environment_id]


def list_remediations_for_finding(finding_id: str, environment_id: str | None = None) -> list[RemediationTask]:
    """Return remediation tasks for a specific finding."""

    active_environment_id = normalize_environment_id(environment_id)
    return [task for task in _active_remediations().values() if task.finding_id == finding_id and task.environment_id == active_environment_id]


def list_policies() -> list[Policy]:
    """Return all posture policies."""

    return list(_DEMO_POLICIES.values())


def list_reports() -> list[Report]:
    """Return all posture reports."""

    return list(_DEMO_REPORTS.values())


def list_telemetry_summaries(environment_id: str | None = None) -> list[TelemetrySummary]:
    """Return telemetry summaries for the active mode without mixing sources."""

    active_environment_id = normalize_environment_id(environment_id)
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_TELEMETRY_SUMMARIES:
            return {summary.id: summary for summary in db.list_records("telemetry_summaries", TelemetrySummary, active_environment_id)}
        return [summary for summary in _TRACKING_TELEMETRY_SUMMARIES.values() if summary.environment_id == active_environment_id]

    return [summary for summary in _DEMO_TELEMETRY_SUMMARIES.values() if summary.environment_id == active_environment_id]


def list_alerts(environment_id: str | None = None) -> list[Alert]:
    """Return environment-scoped SOC and NOC alerts."""

    active_environment_id = normalize_environment_id(environment_id)
    return [alert for alert in _active_alerts().values() if alert.environment_id == active_environment_id]


def list_security_signals(environment_id: str | None = None) -> list[SecuritySignal]:
    """Return environment-scoped security signals."""

    active_environment_id = normalize_environment_id(environment_id)
    return [signal for signal in _active_security_signals().values() if signal.environment_id == active_environment_id]


def list_incidents(environment_id: str | None = None) -> list[IncidentSummary]:
    """Return environment-scoped incident summaries."""

    active_environment_id = normalize_environment_id(environment_id)
    return [incident for incident in _active_incidents().values() if incident.environment_id == active_environment_id]


def list_service_health(environment_id: str | None = None) -> list[ServiceHealth]:
    """Return environment-scoped service health records."""

    active_environment_id = normalize_environment_id(environment_id)
    return [service for service in _active_service_health().values() if service.environment_id == active_environment_id]


def list_dependencies(environment_id: str | None = None) -> list[DependencyStatus]:
    """Return environment-scoped dependency status records."""

    active_environment_id = normalize_environment_id(environment_id)
    return [dependency for dependency in _active_dependencies().values() if dependency.environment_id == active_environment_id]


def list_telemetry_source_health(environment_id: str | None = None) -> list[TelemetrySourceHealth]:
    """Return environment-scoped telemetry source health records."""

    active_environment_id = normalize_environment_id(environment_id)
    return [source for source in _active_telemetry_source_health().values() if source.environment_id == active_environment_id]


def overview_aggregates(environment_id: str | None = None) -> dict[str, object]:
    """Return overview counters for SOC, NOC, and telemetry health."""

    alerts = list_alerts(environment_id)
    signals = list_security_signals(environment_id)
    incidents = list_incidents(environment_id)
    services = list_service_health(environment_id)
    telemetry_sources = list_telemetry_source_health(environment_id)
    return {
        "active_alerts_count": sum(1 for alert in alerts if alert.status in {"active", "firing", "new"}),
        "critical_signals_count": sum(1 for signal in signals if signal.severity == FindingSeverity.CRITICAL and signal.status != "closed"),
        "degraded_services_count": sum(1 for service in services if service.status in {"degraded", "down", "unavailable"}),
        "telemetry_source_health_summary": {
            "healthy": sum(1 for source in telemetry_sources if source.status == "healthy"),
            "degraded": sum(1 for source in telemetry_sources if source.status == "degraded"),
            "unavailable": sum(1 for source in telemetry_sources if source.status == "unavailable"),
            "total": len(telemetry_sources),
        },
        "incident_summary_counts": {
            "open": sum(1 for incident in incidents if incident.status == "open"),
            "triaged": sum(1 for incident in incidents if incident.status == "triaged"),
            "closed": sum(1 for incident in incidents if incident.status == "closed"),
            "total": len(incidents),
        },
    }


def risk_by_asset(environment_id: str | None = None) -> list[RiskByAsset]:
    """Return asset risk with open and critical finding counts."""

    active_environment_id = normalize_environment_id(environment_id)
    output: list[RiskByAsset] = []
    for asset in list_assets(active_environment_id):
        asset_findings = list_findings_for_asset(asset.id, active_environment_id)
        open_findings = [finding for finding in asset_findings if finding.status != "accepted"]
        output.append(
            RiskByAsset(
                asset_id=asset.id,
                asset_name=asset.name,
                open_findings=len(open_findings),
                critical_count=sum(1 for finding in open_findings if finding.severity == FindingSeverity.CRITICAL),
                high_count=sum(1 for finding in open_findings if finding.severity == FindingSeverity.HIGH),
                aggregate_score=calculate_asset_risk(asset.id, open_findings, asset),
            )
        )

    return sorted(output, key=lambda item: item.aggregate_score, reverse=True)


def list_risky_assets(environment_id: str | None = None) -> list[RiskByAsset]:
    """Return assets sorted by aggregate finding risk score."""

    return risk_by_asset(environment_id)


def findings_count_by_severity(environment_id: str | None = None) -> list[FindingSeverityCount]:
    """Return finding counts grouped by severity."""

    active_findings = list_findings(environment_id)
    return [
        FindingSeverityCount(
            severity=severity,
            count=sum(1 for finding in active_findings if finding.severity == severity),
        )
        for severity in FindingSeverity
    ]


def remediation_completion_percentage(environment_id: str | None = None) -> int:
    """Return the percentage of remediation tasks marked completed."""

    tasks = list_remediations(environment_id)
    if not tasks:
        return 0

    completed = sum(1 for task in tasks if task.status == "completed")
    return round((completed / len(tasks)) * 100)


def _active_assets() -> dict[str, Asset]:
    """Return demo or tracking assets based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_ASSETS:
            return {asset.id: asset for asset in db.list_records("assets", Asset)}
        return _TRACKING_ASSETS

    return _DEMO_ASSETS


def _active_inventory() -> dict[str, InventoryRecord]:
    """Return demo or tracking inventory based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_INVENTORY:
            return {record.inventory_id: record for record in db.list_records("inventory", InventoryRecord)}
        return _TRACKING_INVENTORY

    return _DEMO_INVENTORY


def _active_findings() -> dict[str, Finding]:
    """Return demo or tracking findings based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_FINDINGS:
            return {finding.id: finding for finding in db.list_records("findings", Finding)}
        return _TRACKING_FINDINGS

    return _DEMO_FINDINGS


def _active_remediations() -> dict[str, RemediationTask]:
    """Return demo or tracking remediation tasks based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_REMEDIATIONS:
            return {task.id: task for task in db.list_records("remediations", RemediationTask)}
        return _TRACKING_REMEDIATIONS

    return _DEMO_REMEDIATIONS


def _active_alerts() -> dict[str, Alert]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_ALERTS:
            return {alert.alert_id: alert for alert in db.list_records("alerts", Alert)}
        return _TRACKING_ALERTS
    return _DEMO_ALERTS


def _active_security_signals() -> dict[str, SecuritySignal]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        if db.enabled and not _TRACKING_SECURITY_SIGNALS:
            return {signal.signal_id: signal for signal in db.list_records("signals", SecuritySignal)}
        return _TRACKING_SECURITY_SIGNALS
    return _DEMO_SECURITY_SIGNALS


def _active_incidents() -> dict[str, IncidentSummary]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_INCIDENTS
    return _DEMO_INCIDENTS


def _active_service_health() -> dict[str, ServiceHealth]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_SERVICE_HEALTH
    return _DEMO_SERVICE_HEALTH


def _active_dependencies() -> dict[str, DependencyStatus]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_DEPENDENCIES
    return _DEMO_DEPENDENCIES


def _active_telemetry_source_health() -> dict[str, TelemetrySourceHealth]:
    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_TELEMETRY_SOURCE_HEALTH
    return _DEMO_TELEMETRY_SOURCE_HEALTH


def _with_current_score(finding: Finding) -> Finding:
    """Return a finding scored against its current asset context."""

    asset = _active_assets().get(finding.asset_id) or _DEMO_ASSETS.get(finding.asset_id)
    return finding.model_copy(update={"score": calculate_finding_score(finding, asset)})


def get_system_mode() -> SystemMode:
    """Return the current posture mode."""

    return _SYSTEM_MODE


def list_automation_runs(environment_id: str | None = None) -> list[AutomationRun]:
    """Return automation runs in newest-first order."""

    active_environment_id = normalize_environment_id(environment_id)
    if db.enabled:
        return list(reversed(db.list_records("automation_runs", AutomationRun, active_environment_id)))
    return [run for run in reversed(_AUTOMATION_RUNS) if run.environment_id == active_environment_id]


def discover_assets(environment_id: str | None = None) -> AutomationRun:
    """Safely derive trackable assets from approved in-memory posture inventory."""

    active_environment_id = normalize_environment_id(environment_id)
    _enable_tracking_mode()
    now = utc_now()
    for asset in [item for item in _DEMO_ASSETS.values() if item.environment_id == active_environment_id]:
        _TRACKING_ASSETS[asset.id] = asset.model_copy(
            update={
                "source": DataSource.TRACKING,
                "last_seen": now,
            }
        )
    for record in [item for item in _DEMO_INVENTORY.values() if item.environment_id == active_environment_id]:
        _TRACKING_INVENTORY[record.inventory_id] = record.model_copy(update={"source": DataSource.TRACKING, "detected_at": now})

    run = _complete_run(
        "discover-assets",
        assets_discovered=sum(1 for asset in _TRACKING_ASSETS.values() if asset.environment_id == active_environment_id),
        findings_created=0,
        environment_id=active_environment_id,
    )
    return run


def derive_findings(environment_id: str | None = None) -> AutomationRun:
    """Safely derive posture findings from known tracked asset metadata."""

    active_environment_id = normalize_environment_id(environment_id)
    if not list_assets(active_environment_id):
        discover_assets(active_environment_id)

    now = utc_now()
    for finding_id in [finding_id for finding_id, finding in _TRACKING_FINDINGS.items() if finding.environment_id == active_environment_id]:
        del _TRACKING_FINDINGS[finding_id]
    for finding in [item for item in _DEMO_FINDINGS.values() if item.environment_id == active_environment_id]:
        if finding.status == "accepted":
            continue
        _TRACKING_FINDINGS[finding.id] = finding.model_copy(
            update={
                "source": DataSource.TRACKING,
                "opened_at": now,
                "updated_at": now,
                "evidence_summary": "Derived from approved inventory metadata and defensive telemetry expectations.",
            }
        )

    for task_id in [task_id for task_id, task in _TRACKING_REMEDIATIONS.items() if task.environment_id == active_environment_id]:
        del _TRACKING_REMEDIATIONS[task_id]
    for task in [item for item in _DEMO_REMEDIATIONS.values() if item.environment_id == active_environment_id]:
        if task.finding_id in _TRACKING_FINDINGS:
            _TRACKING_REMEDIATIONS[task.id] = task.model_copy(update={"source": DataSource.TRACKING, "updated_at": now})

    run = _complete_run("derive-findings", assets_discovered=0, findings_created=len(list_findings(active_environment_id)), environment_id=active_environment_id)
    return run


def run_inventory_match(environment_id: str | None = None) -> AutomationRun:
    """Match approved inventory records to the seeded CVE knowledge base."""

    active_environment_id = normalize_environment_id(environment_id)
    _enable_tracking_mode()
    if not list_assets(active_environment_id):
        discover_assets(active_environment_id)
    if not list_inventory(active_environment_id):
        now = utc_now()
        for record in [item for item in _DEMO_INVENTORY.values() if item.environment_id == active_environment_id]:
            _TRACKING_INVENTORY[record.inventory_id] = record.model_copy(update={"source": DataSource.TRACKING, "detected_at": now})

    matches = _sync_inventory_match_findings(active_environment_id)
    run = _complete_run("inventory-match", assets_discovered=0, findings_created=len(matches), environment_id=active_environment_id)
    return run


def _sync_inventory_match_findings(environment_id: str) -> list[Finding]:
    matches = list_vulnerability_matches(environment_id)
    _replace_cve_findings(environment_id, matches)
    return matches


def _replace_cve_findings(environment_id: str, matches: list[Finding]) -> None:
    prefix = f"{_CVE_FINDING_PREFIX}-{environment_id}-"
    for finding_id in [finding_id for finding_id in _TRACKING_FINDINGS if finding_id.startswith(prefix)]:
        del _TRACKING_FINDINGS[finding_id]
    for finding in matches:
        _TRACKING_FINDINGS[finding.id] = finding.model_copy(update={"source": DataSource.TRACKING, "updated_at": utc_now()})


def refresh_posture(environment_id: str | None = None) -> AutomationRun:
    """Safely refresh tracking telemetry summaries from current in-memory tracking data."""

    active_environment_id = normalize_environment_id(environment_id)
    if not list_assets(active_environment_id):
        discover_assets(active_environment_id)
    if not list_findings(active_environment_id):
        derive_findings(active_environment_id)

    now = utc_now()
    for summary_id in [summary_id for summary_id, summary in _TRACKING_TELEMETRY_SUMMARIES.items() if summary.environment_id == active_environment_id]:
        del _TRACKING_TELEMETRY_SUMMARIES[summary_id]
    _TRACKING_TELEMETRY_SUMMARIES.update(
        {
            f"{active_environment_id}-tracking-runtime": TelemetrySummary(
                id=f"{active_environment_id}-tracking-runtime",
                environment_id=active_environment_id,
                source_name="Approved runtime tracking",
                source_type="runtime",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "container-runtime" in asset.telemetry_sources or "osquery" in asset.telemetry_sources),
                event_count=len(list_assets(active_environment_id)) * 42,
                health_status="ready",
                updated_at=now,
                notes=["Tracking summary is derived from approved in-memory asset metadata."],
            ),
            f"{active_environment_id}-tracking-network": TelemetrySummary(
                id=f"{active_environment_id}-tracking-network",
                environment_id=active_environment_id,
                source_name="Approved network tracking",
                source_type="network",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "firewall" in asset.telemetry_sources or "dns" in asset.telemetry_sources),
                event_count=len(list_findings(active_environment_id)) * 31,
                health_status="ready",
                updated_at=now,
                notes=["No active probing is performed; counts are posture-derived."],
            ),
            f"{active_environment_id}-tracking-infrastructure": TelemetrySummary(
                id=f"{active_environment_id}-tracking-infrastructure",
                environment_id=active_environment_id,
                source_name="Approved infrastructure tracking",
                source_type="infrastructure",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "audit" in asset.telemetry_sources or "prometheus" in asset.telemetry_sources),
                event_count=len(list_remediations(active_environment_id)) * 24,
                health_status="ready",
                updated_at=now,
                notes=["Infrastructure tracking uses defensive inventory and remediation state only."],
            ),
        }
    )
    _sync_prometheus_tracking(active_environment_id)
    _sync_loki_tracking(active_environment_id)
    _sync_inventory_match_findings(active_environment_id)
    _sync_operational_tracking(active_environment_id)

    run = _complete_run("refresh-posture", assets_discovered=0, findings_created=0, environment_id=active_environment_id)
    return run


def run_tracking_cycle(environment_id: str | None = None) -> AutomationRun:
    """Run the full safe tracking cycle without external commands or offensive actions."""

    active_environment_id = normalize_environment_id(environment_id)
    _enable_tracking_mode()
    now = utc_now()

    for asset_id in [asset_id for asset_id, asset in _TRACKING_ASSETS.items() if asset.environment_id == active_environment_id]:
        del _TRACKING_ASSETS[asset_id]
    for asset in [item for item in _DEMO_ASSETS.values() if item.environment_id == active_environment_id]:
        _TRACKING_ASSETS[asset.id] = asset.model_copy(update={"source": DataSource.TRACKING, "last_seen": now})

    for inventory_id in [inventory_id for inventory_id, record in _TRACKING_INVENTORY.items() if record.environment_id == active_environment_id]:
        del _TRACKING_INVENTORY[inventory_id]
    for record in [item for item in _DEMO_INVENTORY.values() if item.environment_id == active_environment_id]:
        _TRACKING_INVENTORY[record.inventory_id] = record.model_copy(update={"source": DataSource.TRACKING, "detected_at": now})

    for finding_id in [finding_id for finding_id, finding in _TRACKING_FINDINGS.items() if finding.environment_id == active_environment_id]:
        del _TRACKING_FINDINGS[finding_id]
    for finding in [item for item in _DEMO_FINDINGS.values() if item.environment_id == active_environment_id]:
        if finding.status == "accepted":
            continue
        _TRACKING_FINDINGS[finding.id] = finding.model_copy(
            update={
                "source": DataSource.TRACKING,
                "opened_at": now,
                "updated_at": now,
                "evidence_summary": "Derived during a safe tracking cycle from approved posture metadata.",
            }
        )

    for task_id in [task_id for task_id, task in _TRACKING_REMEDIATIONS.items() if task.environment_id == active_environment_id]:
        del _TRACKING_REMEDIATIONS[task_id]
    for task in [item for item in _DEMO_REMEDIATIONS.values() if item.environment_id == active_environment_id]:
        if task.finding_id in _TRACKING_FINDINGS:
            _TRACKING_REMEDIATIONS[task.id] = task.model_copy(update={"source": DataSource.TRACKING, "updated_at": now})

    for summary_id in [summary_id for summary_id, summary in _TRACKING_TELEMETRY_SUMMARIES.items() if summary.environment_id == active_environment_id]:
        del _TRACKING_TELEMETRY_SUMMARIES[summary_id]
    _TRACKING_TELEMETRY_SUMMARIES.update(
        {
            f"{active_environment_id}-tracking-runtime": TelemetrySummary(
                id=f"{active_environment_id}-tracking-runtime",
                environment_id=active_environment_id,
                source_name="Approved runtime tracking",
                source_type="runtime",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "container-runtime" in asset.telemetry_sources or "osquery" in asset.telemetry_sources),
                event_count=len(list_assets(active_environment_id)) * 42,
                health_status="ready",
                updated_at=now,
                notes=["Tracking cycle completed using in-memory defensive metadata."],
            ),
            f"{active_environment_id}-tracking-network": TelemetrySummary(
                id=f"{active_environment_id}-tracking-network",
                environment_id=active_environment_id,
                source_name="Approved network tracking",
                source_type="network",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "firewall" in asset.telemetry_sources or "dns" in asset.telemetry_sources),
                event_count=len(list_findings(active_environment_id)) * 31,
                health_status="ready",
                updated_at=now,
                notes=["No scanning or probing was performed."],
            ),
            f"{active_environment_id}-tracking-infrastructure": TelemetrySummary(
                id=f"{active_environment_id}-tracking-infrastructure",
                environment_id=active_environment_id,
                source_name="Approved infrastructure tracking",
                source_type="infrastructure",
                source=DataSource.TRACKING,
                asset_count=sum(1 for asset in list_assets(active_environment_id) if "audit" in asset.telemetry_sources or "prometheus" in asset.telemetry_sources),
                event_count=len(list_remediations(active_environment_id)) * 24,
                health_status="ready",
                updated_at=now,
                notes=["Posture score is calculated from tracked findings and remediations."],
            ),
        }
    )
    _sync_prometheus_tracking(active_environment_id)
    _sync_loki_tracking(active_environment_id)
    _sync_inventory_match_findings(active_environment_id)
    _sync_operational_tracking(active_environment_id)

    run = _complete_run(
        "tracking-cycle",
        assets_discovered=len(list_assets(active_environment_id)),
        findings_created=len(list_findings(active_environment_id)),
        environment_id=active_environment_id,
    )
    _SYSTEM_MODE.last_tracking_run_at = run.completed_at
    return run


def _enable_tracking_mode() -> None:
    """Switch to tracking mode without mixing demo and tracking stores."""

    _SYSTEM_MODE.mode = SystemModeName.TRACKING
    _SYSTEM_MODE.tracking_enabled = True


def _complete_run(status: str, assets_discovered: int, findings_created: int, environment_id: str | None = None) -> AutomationRun:
    """Create and store a completed automation run record."""

    active_environment_id = normalize_environment_id(environment_id)
    started_at = utc_now()
    completed_at = utc_now()
    run = AutomationRun(
        run_id=f"run-{len(_AUTOMATION_RUNS) + 1:04d}",
        environment_id=active_environment_id,
        started_at=started_at,
        completed_at=completed_at,
        status=status,
        assets_discovered=assets_discovered,
        findings_created=findings_created,
        posture_score=_posture_score(active_environment_id),
    )
    _AUTOMATION_RUNS.append(run)
    _persist_environment_tracking(active_environment_id)
    if db.enabled:
        db.upsert_many("automation_runs", [run])
    _SYSTEM_MODE.last_tracking_run_at = completed_at
    return run


def _persist_environment_tracking(environment_id: str) -> None:
    """Persist tracking-mode records for one environment when PostgreSQL is configured."""

    if not db.enabled:
        return
    db.replace_environment("assets", environment_id, [asset for asset in _TRACKING_ASSETS.values() if asset.environment_id == environment_id])
    db.replace_environment("findings", environment_id, [finding for finding in _TRACKING_FINDINGS.values() if finding.environment_id == environment_id])
    db.replace_environment("remediations", environment_id, [task for task in _TRACKING_REMEDIATIONS.values() if task.environment_id == environment_id])
    db.replace_environment("inventory", environment_id, [record for record in _TRACKING_INVENTORY.values() if record.environment_id == environment_id])
    db.replace_environment("telemetry_summaries", environment_id, [summary for summary in _TRACKING_TELEMETRY_SUMMARIES.values() if summary.environment_id == environment_id])
    db.replace_environment("alerts", environment_id, [alert for alert in _TRACKING_ALERTS.values() if alert.environment_id == environment_id])
    db.replace_environment("signals", environment_id, [signal for signal in _TRACKING_SECURITY_SIGNALS.values() if signal.environment_id == environment_id])


def _sync_operational_tracking(environment_id: str) -> None:
    """Refresh read-only SOC and NOC tracking records from approved posture state."""

    now = utc_now()
    _replace_environment_records(_TRACKING_ALERTS, environment_id)
    _replace_environment_records(_TRACKING_SECURITY_SIGNALS, environment_id)
    _replace_environment_records(_TRACKING_INCIDENTS, environment_id)
    _replace_environment_records(_TRACKING_SERVICE_HEALTH, environment_id)
    _replace_environment_records(_TRACKING_DEPENDENCIES, environment_id)
    _replace_environment_records(_TRACKING_TELEMETRY_SOURCE_HEALTH, environment_id)

    for alert in [item for item in _DEMO_ALERTS.values() if item.environment_id == environment_id]:
        _TRACKING_ALERTS[alert.alert_id] = alert.model_copy(update={"updated_at": now})
    for signal in [item for item in _DEMO_SECURITY_SIGNALS.values() if item.environment_id == environment_id]:
        _TRACKING_SECURITY_SIGNALS[signal.signal_id] = signal.model_copy(update={"detected_at": now})
    for incident in [item for item in _DEMO_INCIDENTS.values() if item.environment_id == environment_id]:
        _TRACKING_INCIDENTS[incident.incident_id] = incident.model_copy(update={"updated_at": now})
    for service in [item for item in _DEMO_SERVICE_HEALTH.values() if item.environment_id == environment_id]:
        _TRACKING_SERVICE_HEALTH[service.service_id] = service.model_copy(update={"updated_at": now})
    for dependency in [item for item in _DEMO_DEPENDENCIES.values() if item.environment_id == environment_id]:
        _TRACKING_DEPENDENCIES[dependency.dependency_id] = dependency.model_copy(update={"updated_at": now})
    for source in [item for item in _DEMO_TELEMETRY_SOURCE_HEALTH.values() if item.environment_id == environment_id]:
        _TRACKING_TELEMETRY_SOURCE_HEALTH[source.source_id] = source.model_copy(update={"updated_at": now})

    for finding in list_findings(environment_id):
        if finding.source != DataSource.TRACKING or finding.status == "accepted":
            continue
        if finding.category in {"monitoring_gap", "runtime_risk", "network_risk", "exposure"} and finding.score >= 60:
            signal_id = f"signal-{finding.id}"
            _TRACKING_SECURITY_SIGNALS[signal_id] = SecuritySignal(
                signal_id=signal_id,
                environment_id=environment_id,
                source="Telemetry-backed finding",
                category=finding.category,
                title=finding.title,
                severity=finding.severity,
                confidence=finding.confidence,
                asset_id=finding.asset_id,
                evidence=finding.evidence_summary,
                detected_at=now,
                status="new",
            )
        if finding.score >= 75:
            alert_id = f"alert-{finding.id}"
            _TRACKING_ALERTS[alert_id] = Alert(
                alert_id=alert_id,
                environment_id=environment_id,
                source="PurpleClaw",
                title=finding.title,
                severity=finding.severity,
                status="active",
                started_at=now,
                updated_at=now,
                asset_id=finding.asset_id,
            )


def _replace_environment_records(records: dict[str, object], environment_id: str) -> None:
    for record_id in [record_id for record_id, record in records.items() if getattr(record, "environment_id", None) == environment_id]:
        del records[record_id]


def _sync_prometheus_tracking(environment_id: str) -> dict[str, object]:
    """Update Prometheus-backed telemetry and findings for one environment."""

    metrics = get_environment_metrics(environment_id)
    _upsert_prometheus_telemetry_summary(environment_id, metrics)
    _replace_prometheus_findings(environment_id, metrics)
    return metrics


def _upsert_prometheus_telemetry_summary(environment_id: str, metrics: dict[str, object]) -> None:
    target_summary = _as_dict(metrics.get("target_summary"))
    node_summary = _as_dict(metrics.get("node_summary"))
    health = _as_dict(metrics.get("health"))
    config = _as_dict(metrics.get("config"))
    enabled = bool(config.get("enabled"))
    status = str(target_summary.get("status") or health.get("status") or "unknown")
    up_targets = _as_int(target_summary.get("up_target_count"))
    down_targets = _as_int(target_summary.get("down_target_count"))
    active_targets = _as_int(target_summary.get("active_target_count"))
    node_state = "present" if node_summary.get("node_exporter_present") else "missing"

    notes = [
        f"Prometheus Status: {health.get('status', 'unknown')}",
        f"Target Health: {up_targets} up / {down_targets} down",
        f"Node exporter: {node_state}",
    ]
    if not enabled:
        notes.append("Telemetry Ingestion: disabled for this environment")
    elif health.get("healthy"):
        notes.append("Telemetry Ingestion: read-only metrics loaded")
    else:
        notes.append("Telemetry Ingestion: Prometheus API unavailable")

    _TRACKING_TELEMETRY_SUMMARIES[f"{environment_id}-prometheus"] = TelemetrySummary(
        id=f"{environment_id}-prometheus",
        environment_id=environment_id,
        source_name="Prometheus",
        source_type="prometheus",
        source=DataSource.TRACKING,
        asset_count=active_targets,
        event_count=up_targets + down_targets,
        health_status=status,
        updated_at=utc_now(),
        notes=notes,
    )


def _replace_prometheus_findings(environment_id: str, metrics: dict[str, object]) -> None:
    prefix = f"{_PROMETHEUS_FINDING_PREFIX}-{environment_id}-"
    for finding_id in [finding_id for finding_id in _TRACKING_FINDINGS if finding_id.startswith(prefix)]:
        del _TRACKING_FINDINGS[finding_id]

    health = _as_dict(metrics.get("health"))
    config = _as_dict(metrics.get("config"))
    target_summary = _as_dict(metrics.get("target_summary"))
    node_summary = _as_dict(metrics.get("node_summary"))
    if not bool(config.get("enabled")):
        return

    if not health.get("healthy"):
        _add_prometheus_finding(
            environment_id,
            "unavailable",
            "Prometheus telemetry ingestion is unavailable",
            FindingSeverity.MEDIUM,
            "Prometheus API could not be reached for read-only telemetry collection.",
            "Confirm the configured Prometheus endpoint is reachable from the backend.",
        )

    down_targets = _as_int(target_summary.get("down_target_count"))
    if down_targets > 0:
        _add_prometheus_finding(
            environment_id,
            "targets-down",
            "Monitoring target down",
            FindingSeverity.HIGH,
            f"Prometheus reports {down_targets} scrape target(s) down.",
            "Restore scrape health or remove stale targets from service discovery.",
        )

    active_targets = _as_int(target_summary.get("active_target_count"))
    if active_targets > 0 and not bool(target_summary.get("node_exporter_present")):
        _add_prometheus_finding(
            environment_id,
            "exporter-missing",
            "Node exporter missing",
            FindingSeverity.MEDIUM,
            "Prometheus has active scrape targets but no node exporter target was detected.",
            "Add node exporter coverage for hosts that should provide system telemetry.",
        )

    if bool(target_summary.get("node_exporter_present")) and _as_int(target_summary.get("node_exporter_up_count")) == 0:
        _add_prometheus_finding(
            environment_id,
            "node-unavailable",
            "Node telemetry unavailable",
            FindingSeverity.HIGH,
            "Node exporter targets are configured but none are currently healthy.",
            "Restore node exporter target health before relying on host telemetry.",
        )

    cpu_pressure = _as_float(node_summary.get("cpu_pressure_percent"))
    if cpu_pressure is not None and cpu_pressure >= 85:
        _add_prometheus_finding(
            environment_id,
            "high-cpu",
            "High CPU pressure",
            FindingSeverity.HIGH,
            f"Prometheus host metrics show CPU pressure at {cpu_pressure}%.",
            "Investigate sustained CPU pressure and expected workload baselines.",
            category="runtime_risk",
            affected_component="host CPU",
        )

    memory_pressure = _as_float(node_summary.get("memory_pressure_percent"))
    if memory_pressure is not None and memory_pressure >= 85:
        _add_prometheus_finding(
            environment_id,
            "high-memory",
            "High memory pressure",
            FindingSeverity.HIGH,
            f"Prometheus host metrics show memory pressure at {memory_pressure}%.",
            "Investigate memory pressure and confirm alert coverage.",
            category="runtime_risk",
            affected_component="host memory",
        )


def _add_prometheus_finding(
    environment_id: str,
    key: str,
    title: str,
    severity: FindingSeverity,
    evidence: str,
    verification: str,
    category: str = "monitoring_gap",
    affected_component: str | None = "Prometheus telemetry",
) -> None:
    finding_id = f"{_PROMETHEUS_FINDING_PREFIX}-{environment_id}-{key}"
    now = utc_now()
    finding = Finding(
        id=finding_id,
        environment_id=environment_id,
        asset_id=f"{environment_id}-prometheus",
        title=title,
        severity=severity,
        category=category,
        status="open",
        exposure="monitoring coverage gap",
        evidence_summary=evidence,
        verification=verification,
        confidence="high" if severity in {FindingSeverity.CRITICAL, FindingSeverity.HIGH} else "medium",
        affected_component=affected_component,
        source=DataSource.TRACKING,
        opened_at=now,
        updated_at=now,
    )
    _TRACKING_FINDINGS[finding_id] = finding.model_copy(update={"score": calculate_finding_score(finding, None)})


def _sync_loki_tracking(environment_id: str) -> dict[str, object]:
    """Update Loki-backed telemetry and findings for one environment."""

    metrics = get_environment_log_metrics(environment_id)
    _upsert_loki_telemetry_summary(environment_id, metrics)
    _replace_loki_findings(environment_id, metrics)
    return metrics


def _upsert_loki_telemetry_summary(environment_id: str, metrics: dict[str, object]) -> None:
    health = _as_dict(metrics.get("health"))
    config = _as_dict(metrics.get("config"))
    log_sources = _as_dict(metrics.get("log_source_summary"))
    auth = _as_dict(metrics.get("auth_failure_summary"))
    service_errors = _as_dict(metrics.get("service_error_summary"))
    enabled = bool(config.get("enabled"))
    status = str(log_sources.get("status") or health.get("status") or "unknown")
    source_count = _as_int(log_sources.get("source_count"))
    log_events = _as_int(log_sources.get("event_count"))
    auth_events = _as_int(auth.get("event_count"))
    service_error_events = _as_int(service_errors.get("event_count"))
    missing_sources = _as_string_list(log_sources.get("missing_sources"))
    stale_sources = _as_string_list(log_sources.get("stale_sources"))

    notes = [
        f"Log Ingestion: {health.get('status', 'unknown')}",
        f"Log Coverage: {source_count} source(s), {len(missing_sources)} missing expected source(s)",
        f"Authentication Signals: {auth_events} failure event(s)",
        f"Service Error Signals: {service_error_events} error event(s)",
    ]
    if not enabled:
        notes.append("Log Ingestion: disabled for this environment")
    if stale_sources:
        notes.append(f"Log Coverage: {len(stale_sources)} stale source(s)")

    _TRACKING_TELEMETRY_SUMMARIES[f"{environment_id}-loki"] = TelemetrySummary(
        id=f"{environment_id}-loki",
        environment_id=environment_id,
        source_name="Loki",
        source_type="loki",
        source=DataSource.TRACKING,
        asset_count=source_count,
        event_count=log_events + auth_events + service_error_events,
        health_status=status,
        updated_at=utc_now(),
        notes=notes,
    )


def _replace_loki_findings(environment_id: str, metrics: dict[str, object]) -> None:
    prefix = f"{_LOKI_FINDING_PREFIX}-{environment_id}-"
    for finding_id in [finding_id for finding_id in _TRACKING_FINDINGS if finding_id.startswith(prefix)]:
        del _TRACKING_FINDINGS[finding_id]

    health = _as_dict(metrics.get("health"))
    config = _as_dict(metrics.get("config"))
    log_sources = _as_dict(metrics.get("log_source_summary"))
    auth = _as_dict(metrics.get("auth_failure_summary"))
    service_errors = _as_dict(metrics.get("service_error_summary"))
    if not bool(config.get("enabled")):
        return

    if not health.get("healthy"):
        _add_loki_finding(
            environment_id,
            "unavailable",
            "Log ingestion unavailable",
            FindingSeverity.MEDIUM,
            "Loki could not be reached for read-only log telemetry collection.",
            "Confirm the configured Loki endpoint is reachable from the backend.",
        )
        return

    missing_sources = _as_string_list(log_sources.get("missing_sources"))
    if missing_sources:
        _add_loki_finding(
            environment_id,
            "missing-source",
            "Missing expected log source",
            FindingSeverity.MEDIUM,
            f"Loki coverage is missing expected source(s): {', '.join(missing_sources)}.",
            "Restore expected log forwarding for the selected environment.",
        )

    auth_events = _as_int(auth.get("event_count"))
    if auth_events >= 5:
        _add_loki_finding(
            environment_id,
            "auth-failures",
            "Repeated authentication failures",
            FindingSeverity.HIGH,
            f"Loki authentication signals include {auth_events} failure event(s) in the review window.",
            "Review identity logs and confirm account lockout and alert coverage.",
            category="exposure",
            affected_component="authentication logs",
        )

    service_error_events = _as_int(service_errors.get("event_count"))
    if service_error_events >= 10:
        _add_loki_finding(
            environment_id,
            "service-errors",
            "Elevated service error rate",
            FindingSeverity.MEDIUM,
            f"Loki service error signals include {service_error_events} error event(s) in the review window.",
            "Review service logs and expected error budgets for the environment.",
            category="runtime_risk",
            affected_component="service logs",
        )

    stale_sources = _as_string_list(log_sources.get("stale_sources"))
    if stale_sources:
        _add_loki_finding(
            environment_id,
            "stale-stream",
            "Stale log stream",
            FindingSeverity.LOW,
            f"Loki has stale log stream(s): {', '.join(stale_sources[:5])}.",
            "Confirm log agents are still forwarding events from expected sources.",
        )


def _add_loki_finding(
    environment_id: str,
    key: str,
    title: str,
    severity: FindingSeverity,
    evidence: str,
    verification: str,
    category: str = "monitoring_gap",
    affected_component: str | None = "Loki log stream",
) -> None:
    finding_id = f"{_LOKI_FINDING_PREFIX}-{environment_id}-{key}"
    now = utc_now()
    finding = Finding(
        id=finding_id,
        environment_id=environment_id,
        asset_id=f"{environment_id}-loki",
        title=title,
        severity=severity,
        category=category,
        status="open",
        exposure="log coverage gap",
        evidence_summary=evidence,
        verification=verification,
        confidence="high" if severity in {FindingSeverity.CRITICAL, FindingSeverity.HIGH} else "medium",
        affected_component=affected_component,
        source=DataSource.TRACKING,
        opened_at=now,
        updated_at=now,
    )
    _TRACKING_FINDINGS[finding_id] = finding.model_copy(update={"score": calculate_finding_score(finding, None)})


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return round(value)
    return 0


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _posture_score(environment_id: str | None = None) -> int:
    """Calculate a simple defensive posture score for active tracking data."""

    assets = list_assets(environment_id)
    findings = list_findings(environment_id)
    remediations = list_remediations(environment_id)
    if not assets:
        return 0

    average_risk = sum(asset.risk_score for asset in assets) / len(assets)
    critical_penalty = sum(10 for finding in findings if finding.severity == FindingSeverity.CRITICAL)
    remediation_credit = remediation_completion_percentage(environment_id) * 0.25 if remediations else 0
    return max(0, min(100, round(100 - average_risk - critical_penalty + remediation_credit)))
