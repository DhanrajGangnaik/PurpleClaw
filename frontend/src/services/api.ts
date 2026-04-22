import axios from 'axios';
import type {
  Asset,
  AutomationRun,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  ManagedEnvironment,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RemediationTask,
  Report,
  SystemMode,
  TelemetrySummaryResponse,
  ValidationResult,
} from '../types/api';
export type {
  Asset,
  AutomationRun,
  ExecuteResponse,
  ExecutionResult,
  ExercisePlan,
  Finding,
  ManagedEnvironment,
  Policy,
  PrometheusConfig,
  PrometheusHealth,
  PrometheusSummary,
  RemediationTask,
  Report,
  SystemMode,
  TelemetrySummaryResponse,
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

export async function getAutomationRuns(environmentId?: string) {
  const response = await api.get<AutomationRun[]>('/automation/runs', { params: environmentParams(environmentId) });
  return response.data;
}

export async function runTrackingCycle(environmentId?: string) {
  const response = await api.post<AutomationRun>('/automation/run-tracking-cycle', undefined, { params: environmentParams(environmentId) });
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
