import enum
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, Float,
    DateTime, JSON, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    admin = "admin"
    analyst = "analyst"
    red_team = "red_team"
    blue_team = "blue_team"
    viewer = "viewer"

class AssetType(str, enum.Enum):
    server = "server"
    workstation = "workstation"
    network_device = "network_device"
    cloud_instance = "cloud_instance"
    container = "container"
    mobile = "mobile"
    iot = "iot"
    database = "database"
    application = "application"
    firewall = "firewall"
    router = "router"
    switch = "switch"

class AssetStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    unknown = "unknown"
    compromised = "compromised"
    quarantined = "quarantined"

class Criticality(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class Severity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

class FindingStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    accepted = "accepted"
    false_positive = "false_positive"

class AlertSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"

class AlertStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"
    suppressed = "suppressed"

class IncidentSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class IncidentStatus(str, enum.Enum):
    new = "new"
    triaged = "triaged"
    investigating = "investigating"
    contained = "contained"
    eradicated = "eradicated"
    recovering = "recovering"
    closed = "closed"

class IOCType(str, enum.Enum):
    ip = "ip"
    domain = "domain"
    hash_md5 = "hash_md5"
    hash_sha1 = "hash_sha1"
    hash_sha256 = "hash_sha256"
    url = "url"
    email = "email"
    file_path = "file_path"
    registry_key = "registry_key"
    certificate = "certificate"
    cve = "cve"

class ScanStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


# ── Auth & Users ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SAEnum(UserRole), default=UserRole.viewer)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))
    key_hash = Column(String(255), unique=True)
    description = Column(String(500))
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(255))
    action = Column(String(255))
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    details = Column(JSON, default={})
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)


# ── Assets ─────────────────────────────────────────────────────────────────────

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SAEnum(AssetType), nullable=False)
    ip_address = Column(String(50))
    hostname = Column(String(255))
    mac_address = Column(String(50))
    os = Column(String(100))
    os_version = Column(String(100))
    status = Column(SAEnum(AssetStatus), default=AssetStatus.active)
    criticality = Column(SAEnum(Criticality), default=Criticality.medium)
    owner = Column(String(255))
    location = Column(String(255))
    department = Column(String(255))
    group_name = Column(String(255))
    tags = Column(JSON, default=[])
    open_ports = Column(JSON, default=[])
    services = Column(JSON, default=[])
    risk_score = Column(Float, default=0.0)
    last_seen = Column(DateTime, nullable=True)
    notes = Column(Text)
    asset_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    findings = relationship("Finding", back_populates="asset")


# ── Vulnerabilities & Findings ─────────────────────────────────────────────────

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id = Column(Integer, primary_key=True)
    cve_id = Column(String(50), unique=True, nullable=True, index=True)
    title = Column(String(500))
    description = Column(Text)
    cvss_score = Column(Float)
    cvss_v3_score = Column(Float)
    cvss_vector = Column(String(255))
    severity = Column(SAEnum(Severity))
    cwe_id = Column(String(50))
    affected_products = Column(JSON, default=[])
    references_urls = Column(JSON, default=[])
    patches = Column(JSON, default=[])
    exploit_available = Column(Boolean, default=False)
    exploit_in_wild = Column(Boolean, default=False)
    published_at = Column(DateTime)
    modified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    findings = relationship("Finding", back_populates="vulnerability")


class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"))
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True)
    title = Column(String(500))
    description = Column(Text)
    severity = Column(SAEnum(Severity))
    status = Column(SAEnum(FindingStatus), default=FindingStatus.open)
    risk_score = Column(Float, default=0.0)
    evidence = Column(JSON, default=[])
    remediation = Column(Text)
    source = Column(String(100))
    affected_port = Column(Integer, nullable=True)
    affected_service = Column(String(100), nullable=True)
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    detected_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", back_populates="findings")
    vulnerability = relationship("Vulnerability", back_populates="findings")
    remediation_tasks = relationship("RemediationTask", back_populates="finding")


class RemediationTask(Base):
    __tablename__ = "remediation_tasks"
    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey("findings.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500))
    description = Column(Text)
    status = Column(String(50), default="open")
    priority = Column(String(50), default="medium")
    due_date = Column(DateTime, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    finding = relationship("Finding", back_populates="remediation_tasks")


# ── Alert Rules & Alerts ───────────────────────────────────────────────────────

class AlertRule(Base):
    __tablename__ = "alert_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    query = Column(Text)
    severity = Column(SAEnum(AlertSeverity))
    rule_type = Column(String(100), default="threshold")
    enabled = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    threshold = Column(Integer, default=1)
    window_minutes = Column(Integer, default=60)
    false_positive_rate = Column(Float, default=0.0)
    match_count = Column(Integer, default=0)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    description = Column(Text)
    severity = Column(SAEnum(AlertSeverity))
    status = Column(SAEnum(AlertStatus), default=AlertStatus.open)
    source = Column(String(100))
    asset_ids = Column(JSON, default=[])
    user_ids = Column(JSON, default=[])
    raw_data = Column(JSON, default={})
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=True)
    rule_name = Column(String(255), nullable=True)
    mitre_techniques = Column(JSON, default=[])
    tags = Column(JSON, default=[])
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


# ── Incidents ──────────────────────────────────────────────────────────────────

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    description = Column(Text)
    severity = Column(SAEnum(IncidentSeverity))
    status = Column(SAEnum(IncidentStatus), default=IncidentStatus.new)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset_ids = Column(JSON, default=[])
    alert_ids = Column(JSON, default=[])
    tlp = Column(String(20), default="TLP:AMBER")
    impact = Column(Text)
    attack_vector = Column(String(255))
    affected_users = Column(Integer, default=0)
    affected_systems = Column(Integer, default=0)
    ioc_ids = Column(JSON, default=[])
    mitre_tactics = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    playbook_ids = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    events = relationship("IncidentEvent", back_populates="incident")
    tasks = relationship("IncidentTask", back_populates="incident")


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255))
    details = Column(Text)
    event_type = Column(String(100), default="note")
    timestamp = Column(DateTime, default=datetime.utcnow)

    incident = relationship("Incident", back_populates="events")


class IncidentTask(Base):
    __tablename__ = "incident_tasks"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500))
    description = Column(Text)
    status = Column(String(50), default="open")
    priority = Column(String(50), default="medium")
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    incident = relationship("Incident", back_populates="tasks")


# ── Cases ──────────────────────────────────────────────────────────────────────

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    title = Column(String(500))
    description = Column(Text)
    status = Column(String(50), default="open")
    priority = Column(String(50), default="medium")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tlp = Column(String(20), default="TLP:GREEN")
    tags = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = relationship("CaseNote", back_populates="case")
    evidence_items = relationship("CaseEvidence", back_populates="case")


class CaseNote(Base):
    __tablename__ = "case_notes"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="notes")


class CaseEvidence(Base):
    __tablename__ = "case_evidence"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    type = Column(String(100))
    name = Column(String(500))
    description = Column(Text)
    file_hash = Column(String(255), nullable=True)
    file_path = Column(String(1000), nullable=True)
    size = Column(Integer, nullable=True)
    chain_of_custody = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="evidence_items")


# ── SIEM / Log Management ──────────────────────────────────────────────────────

class LogSource(Base):
    __tablename__ = "log_sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(100))
    config = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    events_per_day = Column(Integer, default=0)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LogEvent(Base):
    __tablename__ = "log_events"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("log_sources.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    level = Column(String(50))
    category = Column(String(100))
    message = Column(Text)
    raw = Column(Text)
    parsed_fields = Column(JSON, default={})
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    username = Column(String(255), nullable=True)
    source_ip = Column(String(50), nullable=True)
    dest_ip = Column(String(50), nullable=True)
    source_port = Column(Integer, nullable=True)
    dest_port = Column(Integer, nullable=True)
    process_name = Column(String(500), nullable=True)
    tags = Column(JSON, default=[])
    rule_matches = Column(JSON, default=[])


class DetectionRule(Base):
    __tablename__ = "detection_rules"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    logic = Column(Text)
    rule_type = Column(String(100), default="sigma")
    severity = Column(SAEnum(AlertSeverity))
    enabled = Column(Boolean, default=True)
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    false_positive_rate = Column(Float, default=0.0)
    match_count = Column(Integer, default=0)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Threat Intelligence ────────────────────────────────────────────────────────

class ThreatActor(Base):
    __tablename__ = "threat_actors"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    aliases = Column(JSON, default=[])
    description = Column(Text)
    motivation = Column(JSON, default=[])
    sophistication = Column(String(100))
    country = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    ttps = Column(JSON, default=[])
    target_sectors = Column(JSON, default=[])
    tools = Column(JSON, default=[])
    ioc_ids = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    actor_id = Column(Integer, ForeignKey("threat_actors.id"), nullable=True)
    status = Column(String(50), default="active")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    targets = Column(JSON, default=[])
    ttps = Column(JSON, default=[])
    ioc_ids = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class IOC(Base):
    __tablename__ = "iocs"
    id = Column(Integer, primary_key=True)
    type = Column(SAEnum(IOCType))
    value = Column(String(1000), index=True)
    severity = Column(SAEnum(Severity))
    confidence = Column(Integer, default=50)
    tags = Column(JSON, default=[])
    description = Column(Text, nullable=True)
    source = Column(String(255))
    actor_ids = Column(JSON, default=[])
    campaign_ids = Column(JSON, default=[])
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    expired = Column(Boolean, default=False)
    hit_count = Column(Integer, default=0)
    whitelisted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThreatFeed(Base):
    __tablename__ = "threat_feeds"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(100))
    url = Column(String(1000))
    format = Column(String(50))
    enabled = Column(Boolean, default=True)
    api_key_encrypted = Column(String(1000), nullable=True)
    last_fetched = Column(DateTime, nullable=True)
    ioc_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    auto_update = Column(Boolean, default=True)
    update_interval_hours = Column(Integer, default=24)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Red Team ───────────────────────────────────────────────────────────────────

class AttackPlan(Base):
    __tablename__ = "attack_plans"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    objective = Column(Text)
    target_scope = Column(JSON, default=[])
    mitre_tactics = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    team = Column(String(255), nullable=True)
    status = Column(String(50), default="draft")
    authorization_level = Column(String(100), default="assumed_breach")
    rules_of_engagement = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    executions = relationship("AttackExecution", back_populates="plan")


class AttackExecution(Base):
    __tablename__ = "attack_executions"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("attack_plans.id"))
    name = Column(String(255))
    status = Column(String(50), default="pending")
    operator = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    findings_json = Column(JSON, default=[])
    detection_rate = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plan = relationship("AttackPlan", back_populates="executions")
    steps = relationship("AttackStep", back_populates="execution")


class AttackStep(Base):
    __tablename__ = "attack_steps"
    id = Column(Integer, primary_key=True)
    execution_id = Column(Integer, ForeignKey("attack_executions.id"))
    technique_id = Column(String(50))
    step_order = Column(Integer)
    name = Column(String(500))
    description = Column(Text)
    command = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    output = Column(Text, nullable=True)
    detection_triggered = Column(Boolean, default=False)
    blocked = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    execution = relationship("AttackExecution", back_populates="steps")


class ReconRecord(Base):
    __tablename__ = "recon_records"
    id = Column(Integer, primary_key=True)
    target = Column(String(500))
    type = Column(String(100))
    data = Column(JSON, default={})
    source = Column(String(255))
    tags = Column(JSON, default=[])
    plan_id = Column(Integer, ForeignKey("attack_plans.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payload(Base):
    __tablename__ = "payloads"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(100))
    description = Column(Text)
    platform = Column(String(100))
    code_hash = Column(String(255), nullable=True)
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Blue Team ──────────────────────────────────────────────────────────────────

class ThreatHuntingQuery(Base):
    __tablename__ = "threat_hunting_queries"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    query = Column(Text)
    data_source = Column(String(100))
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_run = Column(DateTime, nullable=True)
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EDREvent(Base):
    __tablename__ = "edr_events"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(100))
    severity = Column(SAEnum(AlertSeverity))
    process_name = Column(String(500), nullable=True)
    process_id = Column(Integer, nullable=True)
    parent_process = Column(String(500), nullable=True)
    command_line = Column(Text, nullable=True)
    username = Column(String(255), nullable=True)
    file_path = Column(String(1000), nullable=True)
    target_ip = Column(String(50), nullable=True)
    target_port = Column(Integer, nullable=True)
    rule_name = Column(String(255), nullable=True)
    details = Column(JSON, default={})
    blocked = Column(Boolean, default=False)
    alert_generated = Column(Boolean, default=False)


class FIMRecord(Base):
    __tablename__ = "fim_records"
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    path = Column(String(1000))
    hash_sha256 = Column(String(255), nullable=True)
    hash_md5 = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    permissions = Column(String(100), nullable=True)
    owner = Column(String(255), nullable=True)
    modified_at = Column(DateTime, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="normal")
    baseline_hash = Column(String(255), nullable=True)
    alert_generated = Column(Boolean, default=False)


# ── Purple Team ────────────────────────────────────────────────────────────────

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    type = Column(String(100))
    status = Column(String(50), default="planned")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    red_team = Column(JSON, default=[])
    blue_team = Column(JSON, default=[])
    objectives = Column(JSON, default=[])
    scope = Column(Text, nullable=True)
    mitre_tactics = Column(JSON, default=[])
    detection_rate = Column(Float, default=0.0)
    mean_time_to_detect_minutes = Column(Integer, nullable=True)
    findings = Column(JSON, default=[])
    lessons_learned = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship("ExerciseStep", back_populates="exercise")


class ExerciseStep(Base):
    __tablename__ = "exercise_steps"
    id = Column(Integer, primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    technique_id = Column(String(50))
    step_order = Column(Integer)
    red_action = Column(Text)
    blue_expected = Column(Text, nullable=True)
    detection_success = Column(Boolean, nullable=True)
    detection_time_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="pending")

    exercise = relationship("Exercise", back_populates="steps")


class ATTACKCoverage(Base):
    __tablename__ = "attack_coverage"
    id = Column(Integer, primary_key=True)
    technique_id = Column(String(50), unique=True)
    covered = Column(Boolean, default=False)
    detection_type = Column(String(100), nullable=True)
    control_name = Column(String(255), nullable=True)
    last_tested = Column(DateTime, nullable=True)
    confidence = Column(Integer, default=0)
    notes = Column(Text, nullable=True)


# ── MITRE ATT&CK ───────────────────────────────────────────────────────────────

class MITRETactic(Base):
    __tablename__ = "mitre_tactics"
    id = Column(Integer, primary_key=True)
    tactic_id = Column(String(50), unique=True)
    name = Column(String(255))
    description = Column(Text)
    shortname = Column(String(100))
    url = Column(String(500), nullable=True)


class MITRETechnique(Base):
    __tablename__ = "mitre_techniques"
    id = Column(Integer, primary_key=True)
    technique_id = Column(String(50), unique=True)
    name = Column(String(255))
    description = Column(Text)
    tactic_ids = Column(JSON, default=[])
    platforms = Column(JSON, default=[])
    data_sources = Column(JSON, default=[])
    detection = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    is_subtechnique = Column(Boolean, default=False)
    parent_id = Column(String(50), nullable=True)
    kill_chain_phases = Column(JSON, default=[])


# ── Scans ──────────────────────────────────────────────────────────────────────

class ScanJob(Base):
    __tablename__ = "scan_jobs"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    target = Column(String(500))
    type = Column(String(100))
    policy = Column(String(255))
    scanner = Column(String(100), default="internal")
    status = Column(SAEnum(ScanStatus), default=ScanStatus.pending)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress = Column(Integer, default=0)
    total_hosts = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results = relationship("ScanResult", back_populates="job")


class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("scan_jobs.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    vulnerability_id = Column(Integer, ForeignKey("vulnerabilities.id"), nullable=True)
    severity = Column(SAEnum(Severity))
    title = Column(String(500))
    port = Column(Integer, nullable=True)
    service = Column(String(100), nullable=True)
    details = Column(JSON, default={})
    plugin_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("ScanJob", back_populates="results")


# ── Playbooks ──────────────────────────────────────────────────────────────────

class Playbook(Base):
    __tablename__ = "playbooks"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    type = Column(String(100))
    tags = Column(JSON, default=[])
    mitre_techniques = Column(JSON, default=[])
    steps_json = Column(JSON, default=[])
    estimated_minutes = Column(Integer, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    executions = relationship("PlaybookExecution", back_populates="playbook")


class PlaybookExecution(Base):
    __tablename__ = "playbook_executions"
    id = Column(Integer, primary_key=True)
    playbook_id = Column(Integer, ForeignKey("playbooks.id"))
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    status = Column(String(50), default="running")
    current_step = Column(Integer, default=0)
    step_states = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    playbook = relationship("Playbook", back_populates="executions")


# ── Compliance ─────────────────────────────────────────────────────────────────

class ComplianceFramework(Base):
    __tablename__ = "compliance_frameworks"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    version = Column(String(50))
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    controls_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    controls = relationship("ComplianceControl", back_populates="framework")


class ComplianceControl(Base):
    __tablename__ = "compliance_controls"
    id = Column(Integer, primary_key=True)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id"))
    control_id = Column(String(100))
    name = Column(String(500))
    description = Column(Text)
    category = Column(String(255))
    subcategory = Column(String(255), nullable=True)
    implementation_guidance = Column(Text, nullable=True)
    weight = Column(Float, default=1.0)

    framework = relationship("ComplianceFramework", back_populates="controls")
    assessments = relationship("ComplianceAssessment", back_populates="control")


class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"
    id = Column(Integer, primary_key=True)
    framework_id = Column(Integer, ForeignKey("compliance_frameworks.id"))
    control_id = Column(Integer, ForeignKey("compliance_controls.id"))
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    status = Column(String(50), default="not_assessed")
    evidence = Column(JSON, default=[])
    notes = Column(Text, nullable=True)
    assessed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    assessed_at = Column(DateTime, nullable=True)
    next_review = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)

    control = relationship("ComplianceControl", back_populates="assessments")


# ── Reports ────────────────────────────────────────────────────────────────────

class ReportTemplate(Base):
    __tablename__ = "report_templates"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(100))
    description = Column(Text)
    sections = Column(JSON, default=[])
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=True)
    name = Column(String(255))
    type = Column(String(100))
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    format = Column(String(50), default="pdf")
    file_path = Column(String(1000), nullable=True)
    status = Column(String(50), default="generating")
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    report_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Notifications & Settings ───────────────────────────────────────────────────

class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    type = Column(String(50))
    config = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    last_test_at = Column(DateTime, nullable=True)
    last_test_success = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True)
    value = Column(JSON)
    category = Column(String(100))
    description = Column(String(1000))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
