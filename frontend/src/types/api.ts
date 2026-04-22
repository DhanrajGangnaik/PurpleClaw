export type RiskLevel = 'low' | 'medium' | 'high';
export type Environment = 'endpoint' | 'kubernetes' | 'cloud';
export type ExecutorType = 'atomic' | 'caldera' | 'custom';
export type FindingSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type DataSource = 'demo' | 'tracking';
export type SystemModeName = 'demo' | 'tracking';
export type ManagedEnvironmentType = 'homelab' | 'lab' | 'staging' | 'production';
export type ManagedEnvironmentStatus = 'active' | 'inactive';

export interface ManagedEnvironment {
  environment_id: string;
  name: string;
  type: ManagedEnvironmentType;
  description: string;
  status: ManagedEnvironmentStatus;
  created_at: string;
  updated_at: string;
}

export interface ScopePolicy {
  allowed_targets: string[];
  blocked_targets: string[];
  max_execution_time: number;
}

export interface Technique {
  id: string;
  name: string;
  description: string;
}

export interface ExecutionStep {
  step_id: string;
  description: string;
  executor: ExecutorType;
  command_reference: string;
  safe: boolean;
}

export interface ExpectedTelemetry {
  source: string;
  event_type: string;
  description: string;
}

export interface DetectionExpectation {
  detection_name: string;
  data_source: string;
  severity: string;
  description: string;
}

export interface RollbackStep {
  step_id: string;
  action: string;
}

export interface ExercisePlan {
  id: string;
  created_at?: string;
  updated_at?: string;
  name: string;
  description: string;
  environment: Environment;
  scope: ScopePolicy;
  techniques: Technique[];
  execution_steps: ExecutionStep[];
  expected_telemetry: ExpectedTelemetry[];
  expected_detections: DetectionExpectation[];
  rollback_steps: RollbackStep[];
  risk_level: RiskLevel;
  requires_approval: boolean;
}

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

export interface ExecutionResult {
  execution_id: string;
  environment_id: string;
  created_at: string;
  executed_at: string;
  status: string;
  executor: string;
  message: string;
  plan_id: string;
  executed: boolean;
}

export type ExecuteResponse = ExecutionResult | ValidationResult;

export interface Asset {
  id: string;
  environment_id: string;
  name: string;
  asset_type: string;
  environment: string;
  owner: string;
  exposure: string;
  criticality: string;
  risk_score: number;
  status: string;
  tags: string[];
  telemetry_sources: string[];
  source: DataSource;
  last_seen: string;
}

export interface Finding {
  id: string;
  environment_id: string;
  asset_id: string;
  title: string;
  severity: FindingSeverity;
  category: string;
  status: string;
  exposure: string;
  evidence_summary: string;
  verification: string;
  score: number;
  confidence: 'low' | 'medium' | 'high';
  affected_component: string | null;
  source: DataSource;
  opened_at: string;
  updated_at: string;
}

export interface InventoryRecord {
  inventory_id: string;
  environment_id: string;
  asset_id: string;
  component_name: string;
  component_type: 'package' | 'service' | 'container_image' | 'binary';
  version: string;
  source: DataSource;
  detected_at: string;
}

export interface ThreatAdvisory {
  advisory_id: string;
  source_name: string;
  title: string;
  category: string;
  severity: FindingSeverity;
  published_at: string;
  summary: string;
  affected_products: string[];
  tags: string[];
}

export interface IntelTrend {
  trend_id: string;
  title: string;
  category: string;
  severity: FindingSeverity;
  summary: string;
  affected_technologies: string[];
  updated_at: string;
}

export interface IntelligenceUpdateRun {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  advisories_loaded: number;
  indicators_loaded: number;
  trends_loaded: number;
  findings_reprioritized: number;
}

export interface IntelligenceSummary {
  source_health: {
    status: string;
    source_count: number;
    last_update_at: string | null;
    notes: string;
  };
  relevant_advisories_count: number;
  current_trends_count: number;
  reprioritized_findings_count: number;
  relevant_current_risks: string[];
}

export interface SchedulerJobStatus {
  interval_minutes: number;
  last_run_at: string | null;
  next_run_at: string | null;
  last_status: string;
}

export interface SchedulerStatus {
  enabled: boolean;
  mode: string;
  jobs: Record<'tracking' | 'intelligence' | 'inventory', SchedulerJobStatus>;
}

export interface PlatformHealth {
  api_status: string;
  backend: 'sqlite' | 'postgres';
  enabled: boolean;
  configured: boolean;
  driver_available: boolean;
  database_path?: string | null;
  connection_status: string;
  writable: boolean;
  scheduler: SchedulerStatus;
  environment_count: number;
  metrics: {
    database_size_bytes: number | null;
    record_counts: Record<string, number>;
  };
}

export interface PlatformBackup {
  filename: string;
  size_bytes: number;
  created_at?: string;
  path?: string;
  removed_old_backups?: number;
}

export interface Alert {
  alert_id: string;
  environment_id: string;
  source: string;
  title: string;
  severity: FindingSeverity;
  status: string;
  started_at: string;
  updated_at: string;
  asset_id: string | null;
}

export interface SecuritySignal {
  signal_id: string;
  environment_id: string;
  source: string;
  category: string;
  title: string;
  severity: FindingSeverity;
  confidence: 'low' | 'medium' | 'high';
  asset_id: string | null;
  evidence: string;
  detected_at: string;
  status: string;
}

export interface IncidentSummary {
  incident_id: string;
  environment_id: string;
  title: string;
  severity: FindingSeverity;
  status: string;
  related_signal_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface ServiceHealth {
  service_id: string;
  environment_id: string;
  name: string;
  status: string;
  availability: number;
  latency_ms: number | null;
  error_rate: number | null;
  updated_at: string;
}

export interface DependencyStatus {
  dependency_id: string;
  environment_id: string;
  name: string;
  type: string;
  status: string;
  notes: string;
  updated_at: string;
}

export interface TelemetrySourceHealth {
  source_id: string;
  environment_id: string;
  source_name: string;
  source_type: string;
  status: string;
  last_success_at: string | null;
  notes: string;
  updated_at: string;
}

export interface RemediationTask {
  id: string;
  environment_id: string;
  finding_id: string;
  title: string;
  status: string;
  owner: string;
  due_date: string;
  steps: string[];
  verification: string;
  source: DataSource;
  updated_at: string;
}

export interface Policy {
  id: string;
  name: string;
  domain: string;
  status: string;
  coverage: number;
  requirements: string[];
  source: DataSource;
  last_reviewed: string;
}

export interface Report {
  id: string;
  title: string;
  report_type: string;
  period: string;
  generated_at: string;
  summary: string;
  key_metrics: Record<string, number | string>;
  source: DataSource;
}

export interface TelemetrySummary {
  id: string;
  environment_id: string;
  source_name: string;
  source_type: string;
  source: DataSource;
  asset_count: number;
  event_count: number;
  health_status: string;
  updated_at: string;
  notes: string[];
}

export interface RiskByAsset {
  asset_id: string;
  asset_name: string;
  open_findings: number;
  critical_count: number;
  high_count: number;
  aggregate_score: number;
}

export interface FindingSeverityCount {
  severity: FindingSeverity;
  count: number;
}

export interface OverviewAggregates {
  active_alerts_count: number;
  critical_signals_count: number;
  degraded_services_count: number;
  telemetry_source_health_summary: {
    healthy: number;
    degraded: number;
    unavailable: number;
    total: number;
  };
  incident_summary_counts: {
    open: number;
    triaged: number;
    closed: number;
    total: number;
  };
}

export interface TelemetrySummaryResponse {
  summaries: TelemetrySummary[];
  risk_by_asset: RiskByAsset[];
  findings_by_severity: FindingSeverityCount[];
  remediation_completion_percentage: number;
  overview_aggregates: OverviewAggregates;
}

export interface PrometheusConfig {
  environment_id: string;
  base_url: string;
  enabled: boolean;
  timeout_seconds: number;
}

export interface PrometheusHealth {
  environment_id: string;
  enabled: boolean;
  status: string;
  healthy: boolean;
  message: string;
}

export interface PrometheusTargetSummary {
  environment_id: string;
  status: string;
  active_target_count: number;
  up_target_count: number;
  down_target_count: number;
  node_exporter_present: boolean;
  node_exporter_up_count: number;
  down_targets: string[];
  message: string;
}

export interface PrometheusNodeSummary {
  environment_id: string;
  status: string;
  node_exporter_present: boolean;
  node_exporter_up_count: number;
  cpu_pressure_percent: number | null;
  memory_pressure_percent: number | null;
  disk_pressure_percent: number | null;
  network_bytes_per_second: number | null;
}

export interface PrometheusSummary {
  environment_id: string;
  config: PrometheusConfig;
  health: PrometheusHealth;
  target_summary: PrometheusTargetSummary;
  node_summary: PrometheusNodeSummary;
}

export interface LokiConfig {
  environment_id: string;
  base_url: string;
  enabled: boolean;
  timeout_seconds: number;
}

export interface LokiHealth {
  environment_id: string;
  enabled: boolean;
  status: string;
  healthy: boolean;
  message: string;
}

export interface LokiLogSourceSummary {
  environment_id: string;
  status: string;
  source_count: number;
  active_sources: string[];
  expected_sources: string[];
  missing_sources: string[];
  stale_sources: string[];
  event_count: number;
  newest_log_at: string | null;
  message: string;
}

export interface LokiSignalSummary {
  environment_id: string;
  status: string;
  event_count: number;
  source_count: number;
  sources: string[];
  message: string;
}

export interface LokiSummary {
  environment_id: string;
  config: LokiConfig;
  health: LokiHealth;
  log_source_summary: LokiLogSourceSummary;
  auth_failure_summary: LokiSignalSummary;
  service_error_summary: LokiSignalSummary;
}

export interface SystemMode {
  mode: SystemModeName;
  last_tracking_run_at: string | null;
  tracking_enabled: boolean;
}

export interface AutomationRun {
  run_id: string;
  environment_id: string;
  started_at: string;
  completed_at: string | null;
  status: string;
  assets_discovered: number;
  findings_created: number;
  posture_score: number;
}
