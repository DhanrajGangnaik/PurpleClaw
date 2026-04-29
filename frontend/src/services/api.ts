import axios from 'axios';

const BASE = '/api/v1';

let _token: string | null = null;
export function setToken(t: string | null) { _token = t; }

const ax = axios.create({ baseURL: BASE });
ax.interceptors.request.use((cfg) => {
  if (_token) cfg.headers.Authorization = `Bearer ${_token}`;
  return cfg;
});
ax.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      window.dispatchEvent(new Event('purpleclaw:unauthorized'));
    }
    return Promise.reject(err);
  }
);

const get = <T>(url: string, params?: object) => ax.get<T>(url, { params }).then((r) => r.data);
const post = <T>(url: string, data?: object) => ax.post<T>(url, data).then((r) => r.data);
const put = <T>(url: string, data?: object) => ax.put<T>(url, data).then((r) => r.data);
const patch = <T>(url: string, data?: object) => ax.patch<T>(url, data).then((r) => r.data);
const del = <T>(url: string) => ax.delete<T>(url).then((r) => r.data);

// ─── Types ───────────────────────────────────────────────────────────────────
export interface Paginated<T> { items: T[]; total: number; page: number; size: number; pages: number; }

// Field names match actual SQLAlchemy column names in backend/models.py
export interface Asset { id: number; name: string; hostname: string; ip_address: string; type: string; os: string; os_version: string; status: string; criticality: string; owner: string; location: string; tags: string[]; risk_score: number; asset_metadata: Record<string, unknown>; last_seen: string; created_at: string; }
export interface Vulnerability { id: number; cve_id: string; title: string; description: string; cvss_score: number; severity: string; affected_products: string[]; published_at: string; exploit_available: boolean; patches: string[]; mitre_techniques: string[]; }
export interface Finding { id: number; asset_id: number; vulnerability_id: number; status: string; severity: string; risk_score: number; first_seen: string; last_seen: string; verified: boolean; notes: string; assigned_to: string; }
export interface Alert { id: number; title: string; description: string; severity: string; status: string; source: string; asset_id: number; mitre_technique_id: number; rule_id: number; raw_log: string; created_at: string; updated_at: string; }
// Incident: assignee_id (not assigned_to), resolved_at (not closed_at), no incident_type field
export interface Incident { id: number; title: string; description: string; severity: string; status: string; assignee_id: number | null; asset_ids: number[]; alert_ids: number[]; mitre_tactics: string[]; timeline: unknown[]; created_at: string; updated_at: string; resolved_at: string | null; }
export interface Case { id: number; title: string; description: string; status: string; priority: string; assignee_id: number | null; incident_id: number | null; tlp: string; tags: string[]; created_at: string; updated_at: string; }
export interface LogSource { id: number; name: string; type: string; enabled: boolean; last_seen: string; events_per_day: number; asset_id: number | null; created_at: string; }
export interface LogEvent { id: number; source_id: number; timestamp: string; level: string; category: string; message: string; source_ip: string | null; dest_ip: string | null; username: string | null; process_name: string | null; rule_matches: string[]; raw: string; }
// ThreatActor: country (not origin_country), no mitre_groups field
export interface ThreatActor { id: number; name: string; aliases: string[]; description: string; country: string; motivation: string; sophistication: string; active: boolean; first_seen: string; last_seen: string; ttps: string[]; }
export interface IOC { id: number; type: string; value: string; description: string; confidence: number; severity: string; tags: string[]; source: string; first_seen: string; last_seen: string; active: boolean; threat_actor_id: number | null; }
// Campaign: actor_id (not threat_actor_id), ttps (not techniques)
export interface Campaign { id: number; name: string; description: string; actor_id: number; start_date: string; end_date: string | null; status: string; targets: string[]; ttps: string[]; ioc_ids: number[]; }
// ThreatFeed: type (not feed_type), enabled (not is_active), last_fetched (not last_updated)
export interface ThreatFeed { id: number; name: string; description: string; url: string; type: string; enabled: boolean; last_fetched: string; ioc_count: number; }
// DetectionRule: logic is Text (string), mitre_techniques is JSON array, no mitre_tactic/mitre_technique
export interface DetectionRule { id: number; name: string; description: string; rule_type: string; severity: string; enabled: boolean; logic: string; mitre_techniques: string[]; false_positive_rate: number; created_at: string; }
// AttackPlan: target_scope (not target_asset_ids), created_by_id (not created_by)
export interface AttackPlan { id: number; name: string; description: string; objective: string; target_scope: string; mitre_tactics: string[]; mitre_techniques: string[]; status: string; created_by_id: number; created_at: string; }
// AttackExecution: operator string (not executed_by number)
export interface AttackExecution { id: number; plan_id: number; status: string; started_at: string; completed_at: string | null; operator: string; notes: string; }
// ReconRecord: type (not recon_type), data (not findings), source (not tools_used), created_at (not executed_at)
export interface ReconRecord { id: number; asset_id: number | null; target: string; type: string; data: Record<string, unknown>; source: string; created_at: string; }
// Payload: type (not payload_type), platform (not language), no code/obfuscated/detected_by_av
export interface Payload { id: number; name: string; description: string; type: string; platform: string; tags: string[]; created_at: string; }
// EDREvent: username (not user), rule_name (not mitre_technique), target_ip/target_port, created_at (not timestamp)
export interface EDREvent { id: number; asset_id: number; event_type: string; process_name: string; process_id: number; parent_process: string; command_line: string; file_path: string; target_ip: string | null; target_port: number | null; username: string; severity: string; rule_name: string; created_at: string; }
// FIMRecord: path (not file_path), status (not event_type), checked_at (not timestamp), no hash/size/modified_by
export interface FIMRecord { id: number; asset_id: number; path: string; status: string; checked_at: string; }
// HuntingQuery: data_source (not query_type), mitre_techniques string[] (not mitre_technique string)
export interface HuntingQuery { id: number; name: string; description: string; data_source: string; query: string; mitre_techniques: string[]; created_by: number; created_at: string; }
export interface Exercise { id: number; name: string; description: string; type: string; status: string; start_date: string; end_date: string | null; red_team: string[]; blue_team: string[]; objectives: string[]; created_at: string; }
export interface MitreTactic { id: number; tactic_id: string; name: string; description: string; }
// MitreTechnique: tactic_ids is JSON string[] (not tactic_id: number)
export interface MitreTechnique { id: number; technique_id: string; name: string; description: string; tactic_ids: string[]; platforms: string[]; detection: string; }
// AttackCoverage: technique_id is string like "T1595", covered boolean (not coverage_status string)
export interface AttackCoverage { id: number; technique_id: string; covered: boolean; last_tested: string; notes: string; }
// ScanJob: type (not scan_type), target string (not target_assets array)
export interface ScanJob { id: number; name: string; type: string; status: string; target: string; started_at: string; completed_at: string | null; findings_count: number; policy: string; }
// Playbook: type (not playbook_type), steps_json (not steps), no severity_threshold/is_active
export interface Playbook { id: number; name: string; description: string; type: string; steps_json: unknown[]; created_at: string; }
// PlaybookExecution: step_states (not step_results), no executed_by
export interface PlaybookExecution { id: number; playbook_id: number; incident_id: number | null; status: string; started_at: string; completed_at: string | null; step_states: unknown[]; notes: string; }
// ComplianceFramework: controls_count (not total_controls), no category field
export interface ComplianceFramework { id: number; name: string; version: string; description: string; controls_count: number; }
export interface ComplianceControl { id: number; framework_id: number; control_id: string; title: string; description: string; category: string; criticality: string; }
export interface ComplianceAssessment { id: number; control_id: number; status: string; evidence: string; notes: string; assessed_by: number | null; assessed_at: string | null; next_review: string | null; }
export interface ReportTemplate { id: number; name: string; description: string; template_type: string; sections: string[]; created_at: string; }
// GeneratedReport: name (not title), type (not report_type), created_by_id (not generated_by)
export interface GeneratedReport { id: number; template_id: number | null; name: string; type: string; status: string; created_by_id: number | null; file_path: string | null; report_metadata: Record<string, unknown>; created_at: string; }
export interface AuditLog { id: number; user_id: number | null; action: string; resource_type: string; resource_id: string | null; details: Record<string, unknown>; ip_address: string | null; timestamp: string; }
export interface User { id: number; username: string; email: string; full_name: string; role: string; is_active: boolean; created_at: string; }

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboardStats = () => get<Record<string, unknown>>('/dashboard/stats');
export const getDashboardAlertsTrend = () => get<unknown[]>('/dashboard/alerts-trend');
export const getDashboardTopThreats = () => get<unknown[]>('/dashboard/top-threats');
export const getDashboardAssetRisk = () => get<unknown[]>('/dashboard/asset-risk');
export const getDashboardMitreCoverage = () => get<Record<string, unknown>>('/dashboard/mitre-coverage');

// ─── Assets ───────────────────────────────────────────────────────────────────
export const getAssets = (p = 1, s = 50, q?: string) => get<Paginated<Asset>>('/assets', { page: p, size: s, search: q });
export const getAsset = (id: number) => get<Asset>(`/assets/${id}`);
export const createAsset = (d: Partial<Asset>) => post<Asset>('/assets', d);
export const updateAsset = (id: number, d: Partial<Asset>) => put<Asset>(`/assets/${id}`, d);
export const deleteAsset = (id: number) => del(`/assets/${id}`);
export const getAssetFindings = (id: number) => get<Finding[]>(`/assets/${id}/findings`);

// ─── Vulnerabilities ──────────────────────────────────────────────────────────
export const getVulnerabilities = (p = 1, s = 50) => get<Paginated<Vulnerability>>('/vulns', { page: p, size: s });
export const getVulnerability = (id: number) => get<Vulnerability>(`/vulns/${id}`);

// ─── Findings ─────────────────────────────────────────────────────────────────
export const getFindings = (p = 1, s = 50, status?: string) => get<Paginated<Finding>>('/findings', { page: p, size: s, status });
export const getFinding = (id: number) => get<Finding>(`/findings/${id}`);
export const updateFinding = (id: number, d: Partial<Finding>) => put<Finding>(`/findings/${id}`, d);

// ─── Alerts ───────────────────────────────────────────────────────────────────
export const getAlerts = (p = 1, s = 50, status?: string, severity?: string) => get<Paginated<Alert>>('/alerts', { page: p, size: s, status, severity });
export const getAlert = (id: number) => get<Alert>(`/alerts/${id}`);
export const updateAlert = (id: number, d: Partial<Alert>) => put<Alert>(`/alerts/${id}`, d);

// ─── Incidents ────────────────────────────────────────────────────────────────
export const getIncidents = (p = 1, s = 50, status?: string) => get<Paginated<Incident>>('/incidents', { page: p, size: s, status });
export const getIncident = (id: number) => get<Incident>(`/incidents/${id}`);
export const createIncident = (d: Partial<Incident>) => post<Incident>('/incidents', d);
export const updateIncident = (id: number, d: Partial<Incident>) => put<Incident>(`/incidents/${id}`, d);

// ─── Cases ────────────────────────────────────────────────────────────────────
export const getCases = (p = 1, s = 50) => get<Paginated<Case>>('/cases', { page: p, size: s });
export const getCase = (id: number) => get<Case>(`/cases/${id}`);
export const createCase = (d: Partial<Case>) => post<Case>('/cases', d);
export const updateCase = (id: number, d: Partial<Case>) => put<Case>(`/cases/${id}`, d);

// ─── SIEM ─────────────────────────────────────────────────────────────────────
export const getLogSources = () => get<LogSource[]>('/siem/sources');
export const getLogEvents = (p = 1, s = 100, source_id?: number) => get<Paginated<LogEvent>>('/siem/events', { page: p, size: s, source_id });

// ─── Threat Intel ─────────────────────────────────────────────────────────────
export const getThreatActors = (p = 1, s = 50) => get<Paginated<ThreatActor>>('/intel/actors', { page: p, size: s });
export const getThreatActor = (id: number) => get<ThreatActor>(`/intel/actors/${id}`);
export const getIOCs = (p = 1, s = 100, type?: string) => get<Paginated<IOC>>('/intel/iocs', { page: p, size: s, type });
export const getIOC = (id: number) => get<IOC>(`/intel/iocs/${id}`);
export const createIOC = (d: Partial<IOC>) => post<IOC>('/intel/iocs', d);
export const getCampaigns = (p = 1, s = 50) => get<Paginated<Campaign>>('/intel/campaigns', { page: p, size: s });
export const getThreatFeeds = () => get<ThreatFeed[]>('/intel/feeds');

// ─── Detection Rules ──────────────────────────────────────────────────────────
export const getDetectionRules = (p = 1, s = 50) => get<Paginated<DetectionRule>>('/siem/rules', { page: p, size: s });
export const getDetectionRule = (id: number) => get<DetectionRule>(`/siem/rules/${id}`);
export const createDetectionRule = (d: Partial<DetectionRule>) => post<DetectionRule>('/siem/rules', d);
export const updateDetectionRule = (id: number, d: Partial<DetectionRule>) => put<DetectionRule>(`/siem/rules/${id}`, d);
export const deleteDetectionRule = (id: number) => del(`/siem/rules/${id}`);

// ─── Threat Hunting ───────────────────────────────────────────────────────────
export const getHuntingQueries = (p = 1, s = 50) => get<Paginated<HuntingQuery>>('/blueteam/hunting-queries', { page: p, size: s });
export const createHuntingQuery = (d: Partial<HuntingQuery>) => post<HuntingQuery>('/blueteam/hunting-queries', d);
export const getEDREvents = (p = 1, s = 100) => get<Paginated<EDREvent>>('/blueteam/edr-events', { page: p, size: s });
export const getFIMRecords = (p = 1, s = 100) => get<Paginated<FIMRecord>>('/blueteam/fim', { page: p, size: s });

// ─── Red Team ─────────────────────────────────────────────────────────────────
export const getAttackPlans = (p = 1, s = 50) => get<Paginated<AttackPlan>>('/redteam/plans', { page: p, size: s });
export const getAttackPlan = (id: number) => get<AttackPlan>(`/redteam/plans/${id}`);
export const createAttackPlan = (d: Partial<AttackPlan>) => post<AttackPlan>('/redteam/plans', d);
export const getAttackExecutions = (p = 1, s = 50) => get<Paginated<AttackExecution>>('/redteam/executions', { page: p, size: s });
export const executeAttackPlan = (id: number) => post<AttackExecution>(`/redteam/plans/${id}/execute`);
export const getReconRecords = (p = 1, s = 50) => get<Paginated<ReconRecord>>('/redteam/recon', { page: p, size: s });
export const getPayloads = (p = 1, s = 50) => get<Paginated<Payload>>('/redteam/payloads', { page: p, size: s });

// ─── Purple Team ──────────────────────────────────────────────────────────────
export const getExercises = (p = 1, s = 50) => get<Paginated<Exercise>>('/purpleteam/exercises', { page: p, size: s });
export const getExercise = (id: number) => get<Exercise>(`/purpleteam/exercises/${id}`);
export const getMitreTactics = () => get<MitreTactic[]>('/mitre/tactics');
export const getMitreTechniques = () => get<MitreTechnique[]>('/mitre/techniques');
export const getAttackCoverage = () => get<AttackCoverage[]>('/purpleteam/coverage');
export const updateCoverage = (id: number, d: Partial<AttackCoverage>) => put<AttackCoverage>(`/purpleteam/coverage/${id}`, d);

// ─── Vulnerability Management ─────────────────────────────────────────────────
export const getScanJobs = (p = 1, s = 50) => get<Paginated<ScanJob>>('/scans', { page: p, size: s });
export const createScanJob = (d: Partial<ScanJob>) => post<ScanJob>('/scans', d);
export const getRemediationTasks = (p = 1, s = 50, status?: string) => get<Paginated<unknown>>('/remediation', { page: p, size: s, status });

// ─── Incident Response ────────────────────────────────────────────────────────
export const getPlaybooks = (p = 1, s = 50) => get<Paginated<Playbook>>('/playbooks', { page: p, size: s });
export const getPlaybook = (id: number) => get<Playbook>(`/playbooks/${id}`);
export const getPlaybookExecutions = (p = 1, s = 50) => get<Paginated<PlaybookExecution>>('/playbooks/executions', { page: p, size: s });
export const executePlaybook = (id: number, incident_id?: number) => post<PlaybookExecution>(`/playbooks/${id}/execute`, { incident_id });

// ─── Compliance ───────────────────────────────────────────────────────────────
export const getComplianceFrameworks = () => get<ComplianceFramework[]>('/compliance/frameworks');
export const getComplianceControls = (framework_id: number) => get<ComplianceControl[]>(`/compliance/frameworks/${framework_id}/controls`);
export const getComplianceAssessments = (control_id: number) => get<ComplianceAssessment[]>(`/compliance/controls/${control_id}/assessments`);
export const updateAssessment = (id: number, d: Partial<ComplianceAssessment>) => put<ComplianceAssessment>(`/compliance/assessments/${id}`, d);
export const getComplianceSummary = () => get<Record<string, unknown>>('/compliance/score');

// ─── Reports ──────────────────────────────────────────────────────────────────
export const getReportTemplates = () => get<ReportTemplate[]>('/reports/templates');
export const getReports = (p = 1, s = 50) => get<Paginated<GeneratedReport>>('/reports', { page: p, size: s });
// Backend expects name (not title) and type (not report_type)
export const generateReport = (d: { template_id?: number; name: string; type: string }) => post<GeneratedReport>('/reports/generate', d);

// ─── Settings ─────────────────────────────────────────────────────────────────
export const getUsers = (p = 1, s = 50) => get<Paginated<User>>('/settings/users', { page: p, size: s });
export const createUser = (d: Partial<User> & { password: string }) => post<User>('/settings/users', d);
export const updateUser = (id: number, d: Partial<User>) => put<User>(`/settings/users/${id}`, d);
export const deleteUser = (id: number) => del(`/settings/users/${id}`);
export const getAuditLogs = (p = 1, s = 100) => get<Paginated<AuditLog>>('/settings/audit-logs', { page: p, size: s });
export const getSystemSettings = () => get<Record<string, unknown>[]>('/settings/system');
export const updateSystemSetting = (key: string, value: string) => put('/settings/system', { key, value });

// ─── Engine / Platform ────────────────────────────────────────────────────────
export const getEngineStatus = () => get<Record<string, unknown>>('/engine/status');
export const triggerScan = (mode = 'both') => post<Record<string, unknown>>('/engine/scan', undefined);
export const getPlatformHealth = () => get<Record<string, unknown>>('/platform/health');
