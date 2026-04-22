from collectors.prometheus import get_environment_metrics
from executor.models import ExecutionResult
from planner.schemas import ExercisePlan, utc_now
from posture.models import (
    Asset,
    AutomationRun,
    DataSource,
    Environment,
    Finding,
    FindingSeverity,
    FindingSeverityCount,
    Policy,
    Report,
    RemediationTask,
    RiskByAsset,
    SystemMode,
    SystemModeName,
    TelemetrySummary,
)


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
    ),
    "finding-002": Finding(
        id="finding-002",
        environment_id="homelab",
        asset_id="asset-001",
        title="Firewall deny events lack ownership tags",
        severity=FindingSeverity.MEDIUM,
        category="telemetry",
        status="open",
        exposure="triage delay",
        evidence_summary="Network events are collected but missing service owner enrichment.",
        verification="Sample denied events include owner and asset labels.",
    ),
    "finding-003": Finding(
        id="finding-003",
        environment_id="lab",
        asset_id="asset-002",
        title="Kubernetes audit retention below policy",
        severity=FindingSeverity.HIGH,
        category="logging",
        status="in-progress",
        exposure="reduced investigation window",
        evidence_summary="Audit logs retain seven days while the policy target is thirty days.",
        verification="Validate thirty days of audit events are searchable.",
    ),
    "finding-004": Finding(
        id="finding-004",
        environment_id="lab",
        asset_id="asset-002",
        title="Privileged workload review overdue",
        severity=FindingSeverity.HIGH,
        category="policy",
        status="open",
        exposure="control-plane hardening gap",
        evidence_summary="Two privileged workloads have not been reviewed this quarter.",
        verification="Document approvals and expected runtime constraints.",
    ),
    "finding-005": Finding(
        id="finding-005",
        environment_id="homelab",
        asset_id="asset-003",
        title="Backup verification cadence is inconsistent",
        severity=FindingSeverity.HIGH,
        category="resilience",
        status="open",
        exposure="recovery uncertainty",
        evidence_summary="Recent backups exist, but restore verification results are incomplete.",
        verification="Complete restore validation and capture checksum evidence.",
    ),
    "finding-006": Finding(
        id="finding-006",
        environment_id="homelab",
        asset_id="asset-003",
        title="Storage firmware inventory is stale",
        severity=FindingSeverity.MEDIUM,
        category="asset-hygiene",
        status="open",
        exposure="patch visibility gap",
        evidence_summary="Firmware metadata has not refreshed in more than fourteen days.",
        verification="Refresh inventory and compare against approved baseline.",
    ),
    "finding-007": Finding(
        id="finding-007",
        environment_id="staging",
        asset_id="asset-004",
        title="Container image provenance missing for service workload",
        severity=FindingSeverity.MEDIUM,
        category="supply-chain",
        status="open",
        exposure="unverified package lineage",
        evidence_summary="One service image lacks signed provenance metadata.",
        verification="Attach provenance attestation and verify during deployment.",
    ),
    "finding-008": Finding(
        id="finding-008",
        environment_id="staging",
        asset_id="asset-004",
        title="Runtime detection rule needs validation",
        severity=FindingSeverity.LOW,
        category="validation",
        status="in-progress",
        exposure="detection confidence gap",
        evidence_summary="The expected container drift alert has not been verified this month.",
        verification="Run safe validation plan and record expected telemetry.",
    ),
    "finding-009": Finding(
        id="finding-009",
        environment_id="homelab",
        asset_id="asset-005",
        title="MFA enforcement exception requires review",
        severity=FindingSeverity.CRITICAL,
        category="identity",
        status="open",
        exposure="identity assurance gap",
        evidence_summary="One service account remains outside the current MFA enforcement policy.",
        verification="Remove exception or document compensating controls.",
    ),
    "finding-010": Finding(
        id="finding-010",
        environment_id="homelab",
        asset_id="asset-005",
        title="Authentication alert routing is incomplete",
        severity=FindingSeverity.HIGH,
        category="telemetry",
        status="open",
        exposure="delayed identity response",
        evidence_summary="High-risk authentication alerts do not page the security owner.",
        verification="Trigger safe alert test and confirm route delivery.",
    ),
    "finding-011": Finding(
        id="finding-011",
        environment_id="lab",
        asset_id="asset-006",
        title="SIEM parser coverage missing one source",
        severity=FindingSeverity.MEDIUM,
        category="telemetry",
        status="open",
        exposure="partial detection context",
        evidence_summary="One syslog source is ingested as raw text without parsed fields.",
        verification="Parser extracts host, service, severity, and event action fields.",
    ),
    "finding-012": Finding(
        id="finding-012",
        environment_id="lab",
        asset_id="asset-006",
        title="Alert fatigue threshold needs tuning",
        severity=FindingSeverity.LOW,
        category="operations",
        status="accepted",
        exposure="triage noise",
        evidence_summary="Low priority alert volume increased after onboarding a new service.",
        verification="Tune grouping rules while preserving critical notification paths.",
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
_TRACKING_TELEMETRY_SUMMARIES: dict[str, TelemetrySummary] = {}
_PROMETHEUS_FINDING_PREFIX = "prometheus"


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


def list_findings(environment_id: str | None = None) -> list[Finding]:
    """Return posture findings for the active mode."""

    active_environment_id = normalize_environment_id(environment_id)
    return [finding for finding in _active_findings().values() if finding.environment_id == active_environment_id]


def list_findings_for_asset(asset_id: str, environment_id: str | None = None) -> list[Finding]:
    """Return findings for a specific asset."""

    active_environment_id = normalize_environment_id(environment_id)
    return [finding for finding in _active_findings().values() if finding.asset_id == asset_id and finding.environment_id == active_environment_id]


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
        return [summary for summary in _TRACKING_TELEMETRY_SUMMARIES.values() if summary.environment_id == active_environment_id]

    return [summary for summary in _DEMO_TELEMETRY_SUMMARIES.values() if summary.environment_id == active_environment_id]


def risk_by_asset(environment_id: str | None = None) -> list[RiskByAsset]:
    """Return asset risk with open and critical finding counts."""

    active_environment_id = normalize_environment_id(environment_id)
    output: list[RiskByAsset] = []
    for asset in list_assets(active_environment_id):
        asset_findings = list_findings_for_asset(asset.id, active_environment_id)
        open_findings = [finding for finding in asset_findings if finding.status != "accepted"]
        critical_findings = [finding for finding in open_findings if finding.severity == FindingSeverity.CRITICAL]
        output.append(
            RiskByAsset(
                asset_id=asset.id,
                asset_name=asset.name,
                risk_score=asset.risk_score,
                open_findings=len(open_findings),
                critical_findings=len(critical_findings),
            )
        )

    return sorted(output, key=lambda item: item.risk_score, reverse=True)


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
        return _TRACKING_ASSETS

    return _DEMO_ASSETS


def _active_findings() -> dict[str, Finding]:
    """Return demo or tracking findings based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_FINDINGS

    return _DEMO_FINDINGS


def _active_remediations() -> dict[str, RemediationTask]:
    """Return demo or tracking remediation tasks based on system mode."""

    if _SYSTEM_MODE.mode == SystemModeName.TRACKING:
        return _TRACKING_REMEDIATIONS

    return _DEMO_REMEDIATIONS


def get_system_mode() -> SystemMode:
    """Return the current posture mode."""

    return _SYSTEM_MODE


def list_automation_runs(environment_id: str | None = None) -> list[AutomationRun]:
    """Return automation runs in newest-first order."""

    active_environment_id = normalize_environment_id(environment_id)
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
    _SYSTEM_MODE.last_tracking_run_at = completed_at
    return run


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
        )


def _add_prometheus_finding(environment_id: str, key: str, title: str, severity: FindingSeverity, evidence: str, verification: str) -> None:
    finding_id = f"{_PROMETHEUS_FINDING_PREFIX}-{environment_id}-{key}"
    now = utc_now()
    _TRACKING_FINDINGS[finding_id] = Finding(
        id=finding_id,
        environment_id=environment_id,
        asset_id=f"{environment_id}-prometheus",
        title=title,
        severity=severity,
        category="telemetry",
        status="open",
        exposure="monitoring coverage gap",
        evidence_summary=evidence,
        verification=verification,
        source=DataSource.TRACKING,
        opened_at=now,
        updated_at=now,
    )


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


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
