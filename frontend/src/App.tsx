import { useEffect, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { useFetch } from './hooks/useFetch';
import { Alerts } from './pages/Alerts';
import { Assets } from './pages/Assets';
import { Automation } from './pages/Automation';
import { Dependencies } from './pages/Dependencies';
import { Executions } from './pages/Executions';
import { Findings } from './pages/Findings';
import { Inventory } from './pages/Inventory';
import { Overview } from './pages/Overview';
import { Plans } from './pages/Plans';
import { Policies } from './pages/Policies';
import { Remediation } from './pages/Remediation';
import { Reports } from './pages/Reports';
import { Scheduler } from './pages/Scheduler';
import { Validator } from './pages/Validator';
import { SecuritySignals } from './pages/SecuritySignals';
import { ServiceHealth } from './pages/ServiceHealth';
import {
  getAlerts,
  getAssets,
  getAutomationRuns,
  getDependencies,
  getEnvironments,
  getExecutions,
  getInventory,
  getLokiSummary,
  getPlans,
  getPolicies,
  getPrioritizedFindings,
  getPrometheusSummary,
  getRemediations,
  getReports,
  getRiskyAssets,
  getSecuritySignals,
  getServiceStatus,
  getServiceHealth,
  getSchedulerStatus,
  getSystemMode,
  getTelemetrySummary,
  getTelemetrySourceHealth,
  getVulnerabilityMatches,
  getIntelligenceUpdateRuns,
  getPlatformBackups,
  getPlatformHealth,
} from './services/api';
import type { ManagedEnvironment } from './types/api';

const mobileNav = [
  { path: '/', label: 'Overview' },
  { path: '/assets', label: 'Assets' },
  { path: '/inventory', label: 'Inventory' },
  { path: '/findings', label: 'Findings' },
  { path: '/remediation', label: 'Remediation' },
  { path: '/alerts', label: 'Alerts' },
  { path: '/signals', label: 'Security Signals' },
  { path: '/service-health', label: 'Service Health' },
  { path: '/dependencies', label: 'Dependencies' },
  { path: '/scheduler', label: 'Operations' },
  { path: '/policies', label: 'Policies' },
  { path: '/reports', label: 'Reports' },
  { path: '/automation', label: 'Automation' },
  { path: '/validator', label: 'Validator' },
  { path: '/plans', label: 'Plans' },
  { path: '/executions', label: 'Executions' },
];

function App() {
  const [apiStatus, setApiStatus] = useState<'online' | 'offline'>('offline');
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState(() => localStorage.getItem('purpleclaw.environment_id') ?? 'homelab');
  const environmentsFetch = useFetch(getEnvironments, []);
  const plansFetch = useFetch(() => getPlans(selectedEnvironmentId), [selectedEnvironmentId]);
  const executionsFetch = useFetch(() => getExecutions(selectedEnvironmentId), [selectedEnvironmentId]);
  const assetsFetch = useFetch(() => getAssets(selectedEnvironmentId), [selectedEnvironmentId]);
  const inventoryFetch = useFetch(() => getInventory(selectedEnvironmentId), [selectedEnvironmentId]);
  const vulnerabilityMatchesFetch = useFetch(() => getVulnerabilityMatches(selectedEnvironmentId), [selectedEnvironmentId]);
  const findingsFetch = useFetch(() => getPrioritizedFindings(selectedEnvironmentId), [selectedEnvironmentId]);
  const riskyAssetsFetch = useFetch(() => getRiskyAssets(selectedEnvironmentId), [selectedEnvironmentId]);
  const remediationsFetch = useFetch(() => getRemediations(undefined, selectedEnvironmentId), [selectedEnvironmentId]);
  const policiesFetch = useFetch(getPolicies, []);
  const reportsFetch = useFetch(getReports, []);
  const telemetryFetch = useFetch(() => getTelemetrySummary(selectedEnvironmentId), [selectedEnvironmentId]);
  const prometheusFetch = useFetch(() => getPrometheusSummary(selectedEnvironmentId), [selectedEnvironmentId]);
  const lokiFetch = useFetch(() => getLokiSummary(selectedEnvironmentId), [selectedEnvironmentId]);
  const alertsFetch = useFetch(() => getAlerts(selectedEnvironmentId), [selectedEnvironmentId]);
  const signalsFetch = useFetch(() => getSecuritySignals(selectedEnvironmentId), [selectedEnvironmentId]);
  const serviceHealthFetch = useFetch(() => getServiceHealth(selectedEnvironmentId), [selectedEnvironmentId]);
  const dependenciesFetch = useFetch(() => getDependencies(selectedEnvironmentId), [selectedEnvironmentId]);
  const telemetrySourceHealthFetch = useFetch(() => getTelemetrySourceHealth(selectedEnvironmentId), [selectedEnvironmentId]);
  const schedulerFetch = useFetch(getSchedulerStatus, []);
  const platformHealthFetch = useFetch(getPlatformHealth, []);
  const platformBackupsFetch = useFetch(getPlatformBackups, []);
  const intelligenceRunsFetch = useFetch(getIntelligenceUpdateRuns, []);
  const modeFetch = useFetch(getSystemMode, []);
  const automationRunsFetch = useFetch(() => getAutomationRuns(selectedEnvironmentId), [selectedEnvironmentId]);

  const refreshData = () => {
    void plansFetch.refetch();
    void executionsFetch.refetch();
    void assetsFetch.refetch();
    void inventoryFetch.refetch();
    void vulnerabilityMatchesFetch.refetch();
    void findingsFetch.refetch();
    void riskyAssetsFetch.refetch();
    void remediationsFetch.refetch();
    void policiesFetch.refetch();
    void reportsFetch.refetch();
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
  const selectedEnvironment =
    environments.find((environment) => environment.environment_id === selectedEnvironmentId) ??
    ({ environment_id: selectedEnvironmentId, name: selectedEnvironmentId, type: 'homelab', status: 'active', description: '', created_at: '', updated_at: '' } satisfies ManagedEnvironment);

  const handleEnvironmentChange = (environmentId: string) => {
    setSelectedEnvironmentId(environmentId);
    localStorage.setItem('purpleclaw.environment_id', environmentId);
  };

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
    if (!environments.some((environment) => environment.environment_id === selectedEnvironmentId)) {
      handleEnvironmentChange(environments[0].environment_id);
    }
  }, [environments, selectedEnvironmentId]);

  const plans = plansFetch.data ?? [];
  const executions = executionsFetch.data ?? [];
  const assets = assetsFetch.data ?? [];
  const inventory = inventoryFetch.data ?? [];
  const vulnerabilityMatches = vulnerabilityMatchesFetch.data ?? [];
  const findings = findingsFetch.data ?? [];
  const riskyAssets = riskyAssetsFetch.data ?? [];
  const remediations = remediationsFetch.data ?? [];
  const policies = policiesFetch.data ?? [];
  const reports = reportsFetch.data ?? [];
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
  const postureLoading =
    assetsFetch.loading ||
    inventoryFetch.loading ||
    vulnerabilityMatchesFetch.loading ||
    findingsFetch.loading ||
    riskyAssetsFetch.loading ||
    remediationsFetch.loading ||
    policiesFetch.loading ||
    reportsFetch.loading ||
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
    vulnerabilityMatchesFetch.error ??
    findingsFetch.error ??
    riskyAssetsFetch.error ??
    remediationsFetch.error ??
    policiesFetch.error ??
    reportsFetch.error ??
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

  return (
    <div className="app-shell">
      <div className="app-backdrop fixed inset-0" />
      <div className="app-grid fixed inset-0" />

      <Sidebar />

      <div className="relative lg:pl-72">
        <Header
          apiStatus={apiStatus}
          environments={environments}
          selectedEnvironmentId={selectedEnvironmentId}
          onEnvironmentChange={handleEnvironmentChange}
        />

        <div className="theme-surface-strong border-b px-4 py-3 backdrop-blur-xl sm:px-6 lg:hidden">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {mobileNav.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `rounded-2xl border px-3 py-2 text-center text-sm transition ${
                    isActive
                      ? 'border-fuchsia-400/40 bg-fuchsia-400/10 text-[var(--text-primary)]'
                      : 'theme-inset theme-text-muted'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>

        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route
              path="/"
              element={
                <Overview
                  plans={plans}
                  executions={executions}
                  assets={assets}
                  findings={findings}
                  vulnerabilityMatches={vulnerabilityMatches}
                  riskyAssets={riskyAssets}
                  remediations={remediations}
                  telemetry={telemetry}
                  prometheus={prometheus}
                  loki={loki}
                  alerts={alerts}
                  signals={signals}
                  serviceHealth={serviceHealth}
                  telemetrySourceHealth={telemetrySourceHealth}
                  systemMode={systemMode}
                  automationRuns={automationRuns}
                  selectedEnvironment={selectedEnvironment}
                  loading={plansFetch.loading || executionsFetch.loading}
                  postureLoading={postureLoading}
                  error={environmentsFetch.error ?? plansFetch.error ?? executionsFetch.error ?? postureError}
                  onDataChanged={refreshData}
                />
              }
            />
            <Route
              path="/assets"
              element={<Assets assets={assets} findings={findings} loading={assetsFetch.loading || findingsFetch.loading} error={assetsFetch.error ?? findingsFetch.error} />}
            />
            <Route
              path="/inventory"
              element={
                <Inventory
                  assets={assets}
                  inventory={inventory}
                  vulnerabilityMatches={vulnerabilityMatches}
                  loading={assetsFetch.loading || inventoryFetch.loading || vulnerabilityMatchesFetch.loading}
                  error={assetsFetch.error ?? inventoryFetch.error ?? vulnerabilityMatchesFetch.error}
                />
              }
            />
            <Route
              path="/findings"
              element={<Findings assets={assets} findings={findings} loading={assetsFetch.loading || findingsFetch.loading} error={assetsFetch.error ?? findingsFetch.error} />}
            />
            <Route
              path="/remediation"
              element={
                <Remediation
                  findings={findings}
                  remediations={remediations}
                  loading={findingsFetch.loading || remediationsFetch.loading}
                  error={findingsFetch.error ?? remediationsFetch.error}
                />
              }
            />
            <Route path="/policies" element={<Policies policies={policies} loading={policiesFetch.loading} error={policiesFetch.error} />} />
            <Route path="/reports" element={<Reports reports={reports} loading={reportsFetch.loading} error={reportsFetch.error} />} />
            <Route path="/alerts" element={<Alerts alerts={alerts} assets={assets} loading={alertsFetch.loading || assetsFetch.loading} error={alertsFetch.error ?? assetsFetch.error} />} />
            <Route path="/signals" element={<SecuritySignals signals={signals} assets={assets} loading={signalsFetch.loading || assetsFetch.loading} error={signalsFetch.error ?? assetsFetch.error} />} />
            <Route path="/service-health" element={<ServiceHealth services={serviceHealth} loading={serviceHealthFetch.loading} error={serviceHealthFetch.error} />} />
            <Route path="/dependencies" element={<Dependencies dependencies={dependencies} loading={dependenciesFetch.loading} error={dependenciesFetch.error} />} />
            <Route
              path="/scheduler"
              element={
                <Scheduler
                  selectedEnvironmentId={selectedEnvironmentId}
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
                  selectedEnvironmentId={selectedEnvironmentId}
                  prometheus={prometheus}
                  loki={loki}
                  loading={modeFetch.loading || automationRunsFetch.loading || prometheusFetch.loading || lokiFetch.loading}
                  error={modeFetch.error ?? automationRunsFetch.error ?? prometheusFetch.error ?? lokiFetch.error}
                  onDataChanged={refreshData}
                />
              }
            />
            <Route path="/plans" element={<Plans plans={plans} loading={plansFetch.loading} error={plansFetch.error} />} />
            <Route
              path="/executions"
              element={<Executions executions={executions} loading={executionsFetch.loading} error={executionsFetch.error} />}
            />
            <Route path="/validator" element={<Validator selectedEnvironmentId={selectedEnvironmentId} onDataChanged={refreshData} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
