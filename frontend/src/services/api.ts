import axios from 'axios';
import type {
  Alert,
  Asset,
  AutomationRun,
  DependencyStatus,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  IncidentSummary,
  IntelligenceSummary,
  IntelligenceUpdateRun,
  InventoryRecord,
  IntelTrend,
  LokiConfig,
  LokiHealth,
  LokiSummary,
  ManagedEnvironment,
  PlatformBackup,
  PlatformHealth,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RemediationTask,
  Report,
  RiskByAsset,
  SchedulerStatus,
  SecuritySignal,
  ServiceHealth,
  SystemMode,
  TelemetrySourceHealth,
  TelemetrySummaryResponse,
  ThreatAdvisory,
  ValidationResult,
} from '../types/api';
export type {
  Alert,
  Asset,
  AutomationRun,
  DependencyStatus,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  IncidentSummary,
  IntelligenceSummary,
  IntelligenceUpdateRun,
  InventoryRecord,
  IntelTrend,
  LokiConfig,
  LokiHealth,
  LokiSummary,
  ManagedEnvironment,
  PlatformBackup,
  PlatformHealth,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RemediationTask,
  Report,
  RiskByAsset,
  SchedulerStatus,
  SecuritySignal,
  ServiceHealth,
  SystemMode,
  TelemetrySourceHealth,
  TelemetrySummaryResponse,
  ThreatAdvisory,
  ValidationResult,
} from '../types/api';

export const defaultPlan: ExercisePlan = {
  id: 'plan-1',
  name: 'Test Plan',
  description: 'Basic validation test',
  environment: 'endpoint',
  scope: {
    allowed_targets: ['lab-node-1'],
    blocked_targets: [],
    max_execution_time: 300,
  },
  techniques: [
    {
      id: 'T1059',
      name: 'Command and Scripting Interpreter',
      description: 'Technique example',
    },
  ],
  execution_steps: [
    {
      step_id: 'step-1',
      description: 'Safe stubbed validation step',
      executor: 'custom',
      command_reference: 'ref-safe-001',
      safe: true,
    },
  ],
  expected_telemetry: [
    {
      source: 'sysmon',
      event_type: 'process_create',
      description: 'Expected process creation event',
    },
  ],
  expected_detections: [
    {
      detection_name: 'Suspicious Process Execution',
      data_source: 'sysmon',
      severity: 'medium',
      description: 'Example detection expectation',
    },
  ],
  rollback_steps: [
    {
      step_id: 'rb-1',
      action: 'No-op cleanup',
    },
  ],
  risk_level: 'low',
  requires_approval: false,
};

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? import.meta.env.VITE_API_BASE_URL ?? '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function getServiceStatus() {
  const response = await api.get<Record<string, string>>('/');
  return response.data;
}

function environmentParams(environmentId?: string) {
  return environmentId ? { environment_id: environmentId } : undefined;
}

export async function getEnvironments() {
  const response = await api.get<ManagedEnvironment[]>('/environments');
  return response.data;
}

export async function getPlans(environmentId?: string) {
  const response = await api.get<ExercisePlan[]>('/plans', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getExecutions(environmentId?: string) {
  const response = await api.get<ExecutionResult[]>('/executions', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getSystemMode() {
  const response = await api.get<SystemMode>('/system-mode');
  return response.data;
}

export async function getAssets(environmentId?: string) {
  const response = await api.get<Asset[]>('/assets', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getFindings(assetId?: string, environmentId?: string) {
  const endpoint = assetId ? `/findings/${assetId}` : '/findings';
  const response = await api.get<Finding[]>(endpoint, { params: environmentParams(environmentId) });
  return response.data;
}

export async function getPrioritizedFindings(environmentId?: string) {
  const response = await api.get<Finding[]>('/findings/prioritized', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getRiskyAssets(environmentId?: string) {
  const response = await api.get<RiskByAsset[]>('/assets/risky', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getInventory(environmentId?: string) {
  const response = await api.get<InventoryRecord[]>('/inventory', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getInventoryByAsset(assetId: string, environmentId?: string) {
  const response = await api.get<InventoryRecord[]>(`/inventory/${assetId}`, { params: environmentParams(environmentId) });
  return response.data;
}

export async function getVulnerabilityMatches(environmentId?: string) {
  const response = await api.get<Finding[]>('/vulnerabilities/matches', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getAlerts(environmentId?: string) {
  const response = await api.get<Alert[]>('/alerts', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getSecuritySignals(environmentId?: string) {
  const response = await api.get<SecuritySignal[]>('/signals', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIncidents(environmentId?: string) {
  const response = await api.get<IncidentSummary[]>('/incidents', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getServiceHealth(environmentId?: string) {
  const response = await api.get<ServiceHealth[]>('/service-health', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getDependencies(environmentId?: string) {
  const response = await api.get<DependencyStatus[]>('/dependencies', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getTelemetrySourceHealth(environmentId?: string) {
  const response = await api.get<TelemetrySourceHealth[]>('/telemetry-sources/health', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIntelligenceSummary(environmentId?: string) {
  const response = await api.get<IntelligenceSummary>('/intelligence/summary', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIntelligenceAdvisories(environmentId?: string) {
  const response = await api.get<ThreatAdvisory[]>('/intelligence/advisories', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIntelligenceTrends(environmentId?: string) {
  const response = await api.get<IntelTrend[]>('/intelligence/trends', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIntelligenceRelevantFindings(environmentId?: string) {
  const response = await api.get<Finding[]>('/intelligence/relevant-findings', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getIntelligenceUpdateRuns() {
  const response = await api.get<IntelligenceUpdateRun[]>('/intelligence/update-runs');
  return response.data;
}

export async function getRemediations(findingId?: string, environmentId?: string) {
  const endpoint = findingId ? `/remediations/${findingId}` : '/remediations';
  const response = await api.get<RemediationTask[]>(endpoint, { params: environmentParams(environmentId) });
  return response.data;
}

export async function getPolicies() {
  const response = await api.get<Policy[]>('/policies');
  return response.data;
}

export async function getReports() {
  const response = await api.get<Report[]>('/reports');
  return response.data;
}

export async function getTelemetrySummary(environmentId?: string) {
  const response = await api.get<TelemetrySummaryResponse>('/telemetry-summary', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getPrometheusConfig(environmentId?: string) {
  const response = await api.get<PrometheusConfig>('/integrations/prometheus/config', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getPrometheusHealth(environmentId?: string) {
  const response = await api.get<PrometheusHealth>('/integrations/prometheus/health', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getPrometheusSummary(environmentId?: string) {
  const response = await api.get<PrometheusSummary>('/integrations/prometheus/summary', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getLokiConfig(environmentId?: string) {
  const response = await api.get<LokiConfig>('/integrations/loki/config', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getLokiHealth(environmentId?: string) {
  const response = await api.get<LokiHealth>('/integrations/loki/health', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getLokiSummary(environmentId?: string) {
  const response = await api.get<LokiSummary>('/integrations/loki/summary', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getAutomationRuns(environmentId?: string) {
  const response = await api.get<AutomationRun[]>('/automation/runs', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getSchedulerStatus() {
  const response = await api.get<SchedulerStatus>('/scheduler/status');
  return response.data;
}

export async function getPlatformHealth() {
  const response = await api.get<PlatformHealth>('/platform/health');
  return response.data;
}

export async function getPlatformBackups() {
  const response = await api.get<PlatformBackup[]>('/platform/backups');
  return response.data;
}

export async function createPlatformBackup() {
  const response = await api.post<PlatformBackup>('/platform/backup');
  return response.data;
}

export async function runScheduledTracking(environmentId?: string) {
  const response = await api.post<AutomationRun>('/scheduler/run/tracking', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function runScheduledIntelligence(environmentId?: string) {
  const response = await api.post<IntelligenceUpdateRun>('/scheduler/run/intelligence', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function runScheduledInventory(environmentId?: string) {
  const response = await api.post<AutomationRun>('/scheduler/run/inventory', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function runTrackingCycle(environmentId?: string) {
  const response = await api.post<AutomationRun>('/automation/run-tracking-cycle', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function runInventoryMatch(environmentId?: string) {
  const response = await api.post<AutomationRun>('/automation/run-inventory-match', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function updateIntelligence(environmentId?: string) {
  const response = await api.post<IntelligenceUpdateRun>('/automation/update-intelligence', undefined, { params: environmentParams(environmentId) });
  return response.data;
}

export async function validatePlan(plan: ExercisePlan, environmentId?: string) {
  const response = await api.post<ValidationResult>('/validate-plan', plan, { params: environmentParams(environmentId) });
  return response.data;
}

export async function executeStub(plan: ExercisePlan, environmentId?: string) {
  const response = await api.post<ExecuteResponse>('/execute-stub', plan, { params: environmentParams(environmentId) });
  return response.data;
}

export function isExecutionResult(value: ExecuteResponse): value is ExecutionResult {
  return 'execution_id' in value;
}

export function getErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? JSON.stringify(item)).join('; ');
    }
    if (typeof detail === 'string') {
      return detail;
    }
    return error.message;
  }

  return error instanceof Error ? error.message : 'Unexpected error';
}
