import { Suspense, lazy, useEffect, useState } from 'react';
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { useFetch } from './hooks/useFetch';
import { Alerts } from './pages/Alerts';
import { Automation } from './pages/Automation';
import { DataSources } from './pages/DataSources';
import { Dependencies } from './pages/Dependencies';
import { Executions } from './pages/Executions';
import { Home } from './pages/Home';
import { Plans } from './pages/Plans';
import { Policies } from './pages/Policies';
import { Remediation } from './pages/Remediation';
import { Scheduler } from './pages/Scheduler';
import { ServiceHealth } from './pages/ServiceHealth';
import { Settings } from './pages/Settings';
import { SecuritySignals } from './pages/SecuritySignals';
import { Validator } from './pages/Validator';
import {
  getAlerts,
  getAssets,
  getAutomationRuns,
  getDashboards,
  getDatasources,
  getDependencies,
  getEnvironments,
  getExecutions,
  getFindings,
  getIntelligenceUpdateRuns,
  getInventory,
  getLokiSummary,
  getPlans,
  getPolicies,
  getPlatformBackups,
  getPlatformHealth,
  getPrioritizedFindings,
  getPrometheusSummary,
  getRemediations,
  getReports,
  getReportTemplates,
  getRiskyAssets,
  getScans,
  getScanPolicies,
  getSecuritySignals,
  getServiceHealth,
  getServiceStatus,
  getSchedulerStatus,
  getSystemMode,
  getTelemetrySourceHealth,
  getTelemetrySummary,
  getVulnerabilityMatches,
} from './services/api';
import type { ManagedEnvironment } from './types/api';

const Dashboards = lazy(() => import('./pages/Dashboards').then((module) => ({ default: module.Dashboards })));
const Reports = lazy(() => import('./pages/Reports').then((module) => ({ default: module.Reports })));
const Scans = lazy(() => import('./pages/Scans').then((module) => ({ default: module.Scans })));

const SIDEBAR_STORAGE_KEY = 'purpleclaw.sidebar_collapsed';
const ENVIRONMENT_STORAGE_KEY = 'purpleclaw.environment_id';

function App() {
  const navigate = useNavigate();
  const [apiStatus, setApiStatus] = useState<'online' | 'offline'>('offline');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true');
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState(() => localStorage.getItem(ENVIRONMENT_STORAGE_KEY) ?? '');

  const environmentsFetch = useFetch(getEnvironments, []);
  const plansFetch = useFetch(() => getPlans(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const executionsFetch = useFetch(() => getExecutions(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const assetsFetch = useFetch(() => getAssets(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const inventoryFetch = useFetch(() => getInventory(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const datasourcesFetch = useFetch(() => getDatasources(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const dashboardsFetch = useFetch(() => getDashboards(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const vulnerabilityMatchesFetch = useFetch(() => getVulnerabilityMatches(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const findingsFetch = useFetch(() => getPrioritizedFindings(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const allFindingsFetch = useFetch(() => getFindings(undefined, selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const riskyAssetsFetch = useFetch(() => getRiskyAssets(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const remediationsFetch = useFetch(() => getRemediations(undefined, selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const scanPoliciesFetch = useFetch(() => getScanPolicies(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const scansFetch = useFetch(() => getScans(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const policiesFetch = useFetch(getPolicies, []);
  const reportsFetch = useFetch(getReports, []);
  const reportTemplatesFetch = useFetch(getReportTemplates, []);
  const telemetryFetch = useFetch(() => getTelemetrySummary(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const prometheusFetch = useFetch(() => getPrometheusSummary(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const lokiFetch = useFetch(() => getLokiSummary(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const alertsFetch = useFetch(() => getAlerts(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const signalsFetch = useFetch(() => getSecuritySignals(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const serviceHealthFetch = useFetch(() => getServiceHealth(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const dependenciesFetch = useFetch(() => getDependencies(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const telemetrySourceHealthFetch = useFetch(() => getTelemetrySourceHealth(selectedEnvironmentId || undefined), [selectedEnvironmentId]);
  const schedulerFetch = useFetch(getSchedulerStatus, []);
  const platformHealthFetch = useFetch(getPlatformHealth, []);
  const platformBackupsFetch = useFetch(getPlatformBackups, []);
  const intelligenceRunsFetch = useFetch(getIntelligenceUpdateRuns, []);
  const modeFetch = useFetch(getSystemMode, []);
  const automationRunsFetch = useFetch(() => getAutomationRuns(selectedEnvironmentId || undefined), [selectedEnvironmentId]);

  const refreshData = () => {
    void environmentsFetch.refetch();
    void plansFetch.refetch();
    void executionsFetch.refetch();
    void assetsFetch.refetch();
    void inventoryFetch.refetch();
    void datasourcesFetch.refetch();
    void dashboardsFetch.refetch();
    void vulnerabilityMatchesFetch.refetch();
    void findingsFetch.refetch();
    void allFindingsFetch.refetch();
    void riskyAssetsFetch.refetch();
    void remediationsFetch.refetch();
    void scanPoliciesFetch.refetch();
    void scansFetch.refetch();
    void policiesFetch.refetch();
    void reportsFetch.refetch();
    void reportTemplatesFetch.refetch();
    void telemetryFetch.refetch();
    void prometheusFetch.refetch();
    void lokiFetch.refetch();
    void alertsFetch.refetch();
    void signalsFetch.refetch();
    void serviceHealthFetch.refetch();
    void dependenciesFetch.refetch();
    void telemetrySourceHealthFetch.refetch();
    void schedulerFetch.refetch();
    void platformHealthFetch.refetch();
    void platformBackupsFetch.refetch();
    void intelligenceRunsFetch.refetch();
    void modeFetch.refetch();
    void automationRunsFetch.refetch();
  };

  const environments = environmentsFetch.data ?? [];
  const selectedEnvironment = environments.find((environment) => environment.environment_id === selectedEnvironmentId) ?? environments[0] ?? null;

  const handleEnvironmentChange = (environmentId: string) => {
    setSelectedEnvironmentId(environmentId);
    localStorage.setItem(ENVIRONMENT_STORAGE_KEY, environmentId);
  };

  useEffect(() => {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    let active = true;
    getServiceStatus()
      .then(() => {
        if (active) {
          setApiStatus('online');
        }
      })
      .catch(() => {
        if (active) {
          setApiStatus('offline');
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!environments.length) {
      return;
    }
    if (!selectedEnvironmentId || !environments.some((environment) => environment.environment_id === selectedEnvironmentId)) {
      handleEnvironmentChange(environments[0].environment_id);
    }
  }, [environments, selectedEnvironmentId]);

  const plans = plansFetch.data ?? [];
  const executions = executionsFetch.data ?? [];
  const assets = assetsFetch.data ?? [];
  const inventory = inventoryFetch.data ?? [];
  const datasources = datasourcesFetch.data ?? [];
  const dashboards = dashboardsFetch.data ?? [];
  const vulnerabilityMatches = vulnerabilityMatchesFetch.data ?? [];
  const findings = findingsFetch.data ?? [];
  const allFindings = allFindingsFetch.data ?? [];
  const riskyAssets = riskyAssetsFetch.data ?? [];
  const remediations = remediationsFetch.data ?? [];
  const scanPolicies = scanPoliciesFetch.data ?? [];
  const scans = scansFetch.data ?? [];
  const policies = policiesFetch.data ?? [];
  const reports = reportsFetch.data ?? [];
  const reportTemplates = reportTemplatesFetch.data ?? [];
  const telemetry = telemetryFetch.data ?? null;
  const prometheus = prometheusFetch.data ?? null;
  const loki = lokiFetch.data ?? null;
  const alerts = alertsFetch.data ?? [];
  const signals = signalsFetch.data ?? [];
  const serviceHealth = serviceHealthFetch.data ?? [];
  const dependencies = dependenciesFetch.data ?? [];
  const telemetrySourceHealth = telemetrySourceHealthFetch.data ?? [];
  const schedulerStatus = schedulerFetch.data ?? null;
  const platformHealth = platformHealthFetch.data ?? null;
  const platformBackups = platformBackupsFetch.data ?? [];
  const intelligenceRuns = intelligenceRunsFetch.data ?? [];
  const systemMode = modeFetch.data ?? null;
  const automationRuns = automationRunsFetch.data ?? [];
  const postureScore = riskyAssets.length
    ? Math.max(0, 100 - Math.round(riskyAssets.reduce((total, asset) => total + asset.aggregate_score, 0) / riskyAssets.length))
    : 100;
  const postureLoading =
    assetsFetch.loading ||
    inventoryFetch.loading ||
    datasourcesFetch.loading ||
    dashboardsFetch.loading ||
    vulnerabilityMatchesFetch.loading ||
    findingsFetch.loading ||
    riskyAssetsFetch.loading ||
    remediationsFetch.loading ||
    scanPoliciesFetch.loading ||
    scansFetch.loading ||
    policiesFetch.loading ||
    reportsFetch.loading ||
    reportTemplatesFetch.loading ||
    telemetryFetch.loading ||
    prometheusFetch.loading ||
    lokiFetch.loading ||
    alertsFetch.loading ||
    signalsFetch.loading ||
    serviceHealthFetch.loading ||
    dependenciesFetch.loading ||
    telemetrySourceHealthFetch.loading ||
    schedulerFetch.loading ||
    platformHealthFetch.loading ||
    platformBackupsFetch.loading ||
    intelligenceRunsFetch.loading ||
    modeFetch.loading ||
    automationRunsFetch.loading;
  const postureError =
    assetsFetch.error ??
    inventoryFetch.error ??
    datasourcesFetch.error ??
    dashboardsFetch.error ??
    vulnerabilityMatchesFetch.error ??
    findingsFetch.error ??
    riskyAssetsFetch.error ??
    remediationsFetch.error ??
    scanPoliciesFetch.error ??
    scansFetch.error ??
    policiesFetch.error ??
    reportsFetch.error ??
    reportTemplatesFetch.error ??
    telemetryFetch.error ??
    prometheusFetch.error ??
    lokiFetch.error ??
    alertsFetch.error ??
    signalsFetch.error ??
    serviceHealthFetch.error ??
    dependenciesFetch.error ??
    telemetrySourceHealthFetch.error ??
    schedulerFetch.error ??
    platformHealthFetch.error ??
    platformBackupsFetch.error ??
    intelligenceRunsFetch.error ??
    modeFetch.error ??
    automationRunsFetch.error;

  if (!selectedEnvironment) {
    return <div className="app-shell grid min-h-screen place-items-center px-6 text-center text-sm text-[var(--text-muted)]">Loading environments...</div>;
  }

  return (
    <div className="app-shell">
      <div className="app-backdrop fixed inset-0" />
      <div className="app-grid fixed inset-0" />

      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onToggle={() => setSidebarCollapsed((current) => !current)}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <div className={`relative transition-all duration-300 ${sidebarCollapsed ? 'lg:pl-24' : 'lg:pl-72'}`}>
        <Header
          apiStatus={apiStatus}
          environments={environments}
          selectedEnvironmentId={selectedEnvironment.environment_id}
          onEnvironmentChange={handleEnvironmentChange}
          onCreateEnvironmentRequest={() => navigate('/settings')}
          onManageEnvironmentRequest={() => navigate('/settings')}
          onSidebarToggle={() => setMobileSidebarOpen(true)}
        />

        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route
              path="/home"
              element={
                <Home
                  environments={environments}
                  selectedEnvironment={selectedEnvironment}
                  selectedEnvironmentId={selectedEnvironment.environment_id}
                  dashboards={dashboards}
                  alerts={alerts}
                  scans={scans}
                  reports={reports}
                  datasources={datasources}
                  automationRuns={automationRuns}
                  signals={signals}
                  postureScore={postureScore}
                  loading={postureLoading}
                  onEnvironmentChange={handleEnvironmentChange}
                  onCreateEnvironmentRequest={() => navigate('/settings')}
                  onManageEnvironmentRequest={() => navigate('/settings')}
                />
              }
            />
            <Route
              path="/dashboards"
              element={
                <Suspense fallback={<div className="theme-text-faint py-14 text-center text-sm">Loading dashboards...</div>}>
                  <Dashboards
                    selectedEnvironmentId={selectedEnvironment.environment_id}
                    dashboards={dashboards}
                    datasources={datasources}
                    loading={dashboardsFetch.loading || datasourcesFetch.loading}
                    error={dashboardsFetch.error ?? datasourcesFetch.error}
                    onDataChanged={refreshData}
                  />
                </Suspense>
              }
            />
            <Route path="/alerts" element={<Alerts alerts={alerts} assets={assets} loading={alertsFetch.loading || assetsFetch.loading} error={alertsFetch.error ?? assetsFetch.error} />} />
            <Route
              path="/scans"
              element={
                <Suspense fallback={<div className="theme-text-faint py-14 text-center text-sm">Loading scans...</div>}>
                  <Scans
                    selectedEnvironmentId={selectedEnvironment.environment_id}
                    policies={scanPolicies}
                    scans={scans}
                    loading={scanPoliciesFetch.loading || scansFetch.loading}
                    error={scanPoliciesFetch.error ?? scansFetch.error}
                    onDataChanged={refreshData}
                  />
                </Suspense>
              }
            />
            <Route
              path="/reports"
              element={
                <Suspense fallback={<div className="theme-text-faint py-14 text-center text-sm">Loading reports...</div>}>
                  <Reports
                    selectedEnvironmentId={selectedEnvironment.environment_id}
                    reports={reports}
                    templates={reportTemplates}
                    scans={scans}
                    dashboards={dashboards}
                    loading={reportsFetch.loading || reportTemplatesFetch.loading}
                    error={reportsFetch.error ?? reportTemplatesFetch.error}
                    onDataChanged={refreshData}
                  />
                </Suspense>
              }
            />
            <Route
              path="/datasources"
              element={<DataSources selectedEnvironmentId={selectedEnvironment.environment_id} datasources={datasources} loading={datasourcesFetch.loading} error={datasourcesFetch.error} onDataChanged={refreshData} />}
            />
            <Route
              path="/settings"
              element={
                <Settings
                  environments={environments}
                  selectedEnvironmentId={selectedEnvironment.environment_id}
                  onEnvironmentChange={handleEnvironmentChange}
                  onEnvironmentsChanged={(nextEnvironmentId) => {
                    if (nextEnvironmentId) {
                      handleEnvironmentChange(nextEnvironmentId);
                    }
                    refreshData();
                  }}
                />
              }
            />

            <Route path="/signals" element={<SecuritySignals signals={signals} assets={assets} loading={signalsFetch.loading || assetsFetch.loading} error={signalsFetch.error ?? assetsFetch.error} />} />
            <Route path="/service-health" element={<ServiceHealth services={serviceHealth} loading={serviceHealthFetch.loading} error={serviceHealthFetch.error} />} />
            <Route path="/dependencies" element={<Dependencies dependencies={dependencies} loading={dependenciesFetch.loading} error={dependenciesFetch.error} />} />
            <Route
              path="/scheduler"
              element={
                <Scheduler
                  selectedEnvironmentId={selectedEnvironment.environment_id}
                  status={schedulerStatus}
                  platformHealth={platformHealth}
                  platformBackups={platformBackups}
                  automationRuns={automationRuns}
                  intelligenceRuns={intelligenceRuns}
                  loading={schedulerFetch.loading || platformHealthFetch.loading || platformBackupsFetch.loading || automationRunsFetch.loading || intelligenceRunsFetch.loading}
                  error={schedulerFetch.error ?? platformHealthFetch.error ?? platformBackupsFetch.error ?? automationRunsFetch.error ?? intelligenceRunsFetch.error}
                  onDataChanged={refreshData}
                />
              }
            />
            <Route
              path="/automation"
              element={
                <Automation
                  mode={systemMode}
                  runs={automationRuns}
                  selectedEnvironmentId={selectedEnvironment.environment_id}
                  prometheus={prometheus}
                  loki={loki}
                  loading={modeFetch.loading || automationRunsFetch.loading || prometheusFetch.loading || lokiFetch.loading}
                  error={modeFetch.error ?? automationRunsFetch.error ?? prometheusFetch.error ?? lokiFetch.error}
                  onDataChanged={refreshData}
                />
              }
            />
            <Route path="/plans" element={<Plans plans={plans} loading={plansFetch.loading} error={plansFetch.error} />} />
            <Route path="/executions" element={<Executions executions={executions} loading={executionsFetch.loading} error={executionsFetch.error} />} />
            <Route path="/validator" element={<Validator selectedEnvironmentId={selectedEnvironment.environment_id} onDataChanged={refreshData} />} />
            <Route path="/policies" element={<Policies policies={policies} loading={policiesFetch.loading} error={policiesFetch.error} />} />
            <Route path="/remediation" element={<Remediation findings={allFindings} remediations={remediations} loading={allFindingsFetch.loading || remediationsFetch.loading} error={allFindingsFetch.error ?? remediationsFetch.error} />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
          {postureError ? <div className="theme-error mt-6 rounded-2xl p-4 text-sm">{postureError}</div> : null}
        </main>
      </div>
    </div>
  );
}

export default App;
