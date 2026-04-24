import axios from 'axios';
import type {
  Alert,
  Asset,
  AutomationRun,
  DashboardConfig,
  DataRecord,
  RenderedDashboard,
  DashboardSaveRequest,
  DataSourceCreateRequest,
  DatasourceIngestionJob,
  DataSourceScheduleRequest,
  DataSourceTestRequest,
  DataSourceTestResult,
  DependencyStatus,
  EnvironmentCreateRequest,
  EnvironmentUpdateRequest,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  GenerateReportRequest,
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
  PaginatedDataRecords,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RegisteredDataSource,
  RemediationTask,
  Report,
  ReportPreview,
  ReportTemplate,
  RiskByAsset,
  ScanDetail,
  ScanPolicy,
  ScanPolicyCreateRequest,
  ScanRunRequest,
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
  DashboardConfig,
  DataRecord,
  RenderedDashboard,
  DashboardSaveRequest,
  DataSourceCreateRequest,
  DatasourceIngestionJob,
  DataSourceScheduleRequest,
  DataSourceTestRequest,
  DataSourceTestResult,
  DependencyStatus,
  EnvironmentCreateRequest,
  EnvironmentUpdateRequest,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  GenerateReportRequest,
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
  PaginatedDataRecords,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RegisteredDataSource,
  RemediationTask,
  Report,
  ReportPreview,
  ReportTemplate,
  RiskByAsset,
  ScanDetail,
  ScanPolicy,
  ScanPolicyCreateRequest,
  ScanRunRequest,
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

// Attach stored JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('purpleclaw.auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, signal AuthContext to clear state (no hard reload)
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent('purpleclaw:unauthorized'));
    }
    return Promise.reject(error);
  },
);

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

export async function createEnvironment(payload: EnvironmentCreateRequest) {
  const response = await api.post<ManagedEnvironment>('/environments', payload);
  return response.data;
}

export async function updateEnvironment(environmentId: string, payload: EnvironmentUpdateRequest) {
  const response = await api.put<ManagedEnvironment>(`/environments/${environmentId}`, payload);
  return response.data;
}

export async function deleteEnvironment(environmentId: string) {
  await api.delete(`/environments/${environmentId}`);
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

export async function getReportTemplates() {
  const response = await api.get<ReportTemplate[]>('/report-templates');
  return response.data;
}

export async function generateReport(payload: GenerateReportRequest) {
  const response = await api.post<Report>('/reports/generate', payload);
  return response.data;
}

export async function previewReport(payload: GenerateReportRequest) {
  const response = await api.post<ReportPreview>('/reports/preview', payload);
  return response.data;
}

export function getReportDownloadUrl(reportId: string) {
  const baseUrl = (api.defaults.baseURL ?? '/api').replace(/\/$/, '');
  return `${baseUrl}/reports/${reportId}/download`;
}

export async function getDatasources(environmentId?: string) {
  const response = await api.get<RegisteredDataSource[]>('/datasources', { params: environmentParams(environmentId) });
  return response.data;
}

export async function createDatasource(payload: DataSourceCreateRequest) {
  const response = await api.post<RegisteredDataSource>('/datasources', payload);
  return response.data;
}

export async function testDatasource(payload: DataSourceTestRequest) {
  const response = await api.post<DataSourceTestResult>('/datasources/test', payload);
  return response.data;
}

export async function getDatasourceJobs(environmentId?: string) {
  const response = await api.get<DatasourceIngestionJob[]>('/datasources/jobs', { params: environmentParams(environmentId) });
  return response.data;
}

export async function ingestDatasource(datasourceId: string) {
  const response = await api.post<DatasourceIngestionJob>(`/datasources/${datasourceId}/ingest`);
  return response.data;
}

export async function scheduleDatasource(datasourceId: string, payload: DataSourceScheduleRequest) {
  const response = await api.post<DatasourceIngestionJob>(`/datasources/${datasourceId}/schedule`, payload);
  return response.data;
}

export async function updateDatasourceSchedule(datasourceId: string, payload: DataSourceScheduleRequest) {
  const response = await api.put<DatasourceIngestionJob>(`/datasources/${datasourceId}/schedule`, payload);
  return response.data;
}

export async function disableDatasourceSchedule(datasourceId: string) {
  const response = await api.post<DatasourceIngestionJob>(`/datasources/${datasourceId}/schedule/disable`);
  return response.data;
}

export async function getDatasourceRecords(datasourceId: string, params?: { page?: number; page_size?: number; record_type?: string }) {
  const response = await api.get<PaginatedDataRecords>(`/datasources/${datasourceId}/records`, { params });
  return response.data;
}

export async function getDashboards(environmentId?: string) {
  const response = await api.get<DashboardConfig[]>('/dashboards', { params: environmentParams(environmentId) });
  return response.data;
}

export async function getRenderedDashboard(dashboardId: string) {
  const response = await api.get<RenderedDashboard>(`/dashboards/${dashboardId}/render`);
  return response.data;
}

export async function createDashboard(payload: DashboardSaveRequest) {
  const response = await api.post<DashboardConfig>('/dashboards', payload);
  return response.data;
}

export async function updateDashboard(dashboardId: string, payload: Omit<DashboardSaveRequest, 'environment_id'>) {
  const response = await api.put<DashboardConfig>(`/dashboards/${dashboardId}`, payload);
  return response.data;
}

export async function getScanPolicies(environmentId?: string) {
  const response = await api.get<ScanPolicy[]>('/scan-policies', { params: environmentParams(environmentId) });
  return response.data;
}

export async function createScanPolicy(payload: ScanPolicyCreateRequest) {
  const response = await api.post<ScanPolicy>('/scan-policies', payload);
  return response.data;
}

export async function getScans(environmentId?: string) {
  const response = await api.get<ScanDetail[]>('/scans', { params: environmentParams(environmentId) });
  return response.data;
}

export async function runScan(payload: ScanRunRequest) {
  const response = await api.post<ScanDetail>('/scans/run', payload);
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
