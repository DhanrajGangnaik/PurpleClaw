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
  source: DataSource;
  opened_at: string;
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
  risk_score: number;
  open_findings: number;
  critical_findings: number;
}

export interface FindingSeverityCount {
  severity: FindingSeverity;
  count: number;
}

export interface TelemetrySummaryResponse {
  summaries: TelemetrySummary[];
  risk_by_asset: RiskByAsset[];
  findings_by_severity: FindingSeverityCount[];
  remediation_completion_percentage: number;
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
