import { useState } from 'react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { DataTable, type DataColumn } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { runTrackingCycle } from '../services/api';
import type {
  Asset,
  AutomationRun,
  ExecutionResult,
  ExercisePlan,
  Finding,
  FindingSeverity,
  Alert,
  LokiSummary,
  ManagedEnvironment,
  PrometheusSummary,
  RemediationTask,
  RiskByAsset,
  SecuritySignal,
  ServiceHealth,
  SystemMode,
  TelemetrySourceHealth,
  TelemetrySummaryResponse,
} from '../types/api';
import { formatDate } from '../utils';

interface OverviewProps {
  plans: ExercisePlan[];
  executions: ExecutionResult[];
  assets: Asset[];
  findings: Finding[];
  vulnerabilityMatches: Finding[];
  riskyAssets: RiskByAsset[];
  remediations: RemediationTask[];
  telemetry: TelemetrySummaryResponse | null;
  prometheus: PrometheusSummary | null;
  loki: LokiSummary | null;
  alerts: Alert[];
  signals: SecuritySignal[];
  serviceHealth: ServiceHealth[];
  telemetrySourceHealth: TelemetrySourceHealth[];
  systemMode: SystemMode | null;
  automationRuns: AutomationRun[];
  selectedEnvironment: ManagedEnvironment;
  loading: boolean;
  postureLoading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

const severityColors: Record<FindingSeverity, string> = {
  critical: 'var(--accent-red)',
  high: '#f43f5e',
  medium: 'var(--accent-purple)',
  low: 'var(--accent-cyan)',
  info: 'var(--text-faint)',
};
const categoryColors = ['var(--accent-cyan)', 'var(--accent-purple)', '#818cf8', 'var(--accent-green)', 'var(--accent-red)', '#f59e0b'];

interface TooltipPayload {
  color?: string;
  name?: string;
  value?: number | string;
  payload?: { name?: string };
}

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayload[]; label?: string }) {
  if (!active || !payload?.length) {
    return null;
  }

  const title = label ?? payload[0]?.payload?.name ?? payload[0]?.name ?? 'Value';

  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{title}</div>
      {payload.map((item) => (
        <div key={`${item.name ?? title}-${item.value}`} className="chart-tooltip-row">
          <span className="inline-flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.color ?? 'var(--accent-cyan)' }} />
            {item.name && item.name !== title ? item.name : 'Count'}
          </span>
          <strong className="theme-text-primary">{item.value}</strong>
        </div>
      ))}
    </div>
  );
}

function severityTone(severity: FindingSeverity) {
  if (severity === 'critical' || severity === 'high') {
    return 'red';
  }
  if (severity === 'medium') {
    return 'purple';
  }
  if (severity === 'low') {
    return 'cyan';
  }
  return 'slate';
}

function categoryData(findings: Finding[]) {
  const counts = findings.reduce<Record<string, number>>((items, finding) => {
    items[finding.category] = (items[finding.category] ?? 0) + 1;
    return items;
  }, {});
  return Object.entries(counts).map(([name, value]) => ({ name, value }));
}

function completionPercentage(remediations: RemediationTask[], telemetry: TelemetrySummaryResponse | null) {
  if (telemetry) {
    return telemetry.remediation_completion_percentage;
  }
  if (remediations.length === 0) {
    return 0;
  }
  return Math.round((remediations.filter((task) => task.status === 'completed').length / remediations.length) * 100);
}

export function Overview({
  plans,
  executions,
  assets,
  findings,
  vulnerabilityMatches,
  riskyAssets,
  remediations,
  telemetry,
  prometheus,
  loki,
  alerts,
  signals,
  serviceHealth,
  telemetrySourceHealth,
  systemMode,
  automationRuns,
  selectedEnvironment,
  loading,
  postureLoading,
  error,
  onDataChanged,
}: OverviewProps) {
  const [runningTracking, setRunningTracking] = useState(false);
  const [trackingError, setTrackingError] = useState<string | null>(null);
  const openFindings = findings.filter((finding) => finding.status !== 'accepted');
  const criticalFindings = openFindings.filter((finding) => finding.severity === 'critical');
  const completedRemediations = remediations.filter((task) => task.status === 'completed');
  const severityData =
    telemetry?.findings_by_severity.map((item) => ({ name: item.severity, value: item.count })) ??
    (['critical', 'high', 'medium', 'low', 'info'] as FindingSeverity[]).map((severity) => ({
      name: severity,
      value: findings.filter((finding) => finding.severity === severity).length,
    }));
  const visibleRiskyAssets = (riskyAssets.length ? riskyAssets : telemetry?.risk_by_asset ?? []).slice(0, 5);
  const assetNames = Object.fromEntries(assets.map((asset) => [asset.id, asset.name]));
  const topFindings = [...openFindings].sort((a, b) => {
    const weight: Record<FindingSeverity, number> = { critical: 5, high: 4, medium: 3, low: 2, info: 1 };
    return b.score - a.score || weight[b.severity] - weight[a.severity];
  });
  const progress = completionPercentage(remediations, telemetry);
  const isTrackingMode = systemMode?.mode === 'tracking';
  const trackingSummaries = (telemetry?.summaries ?? []).filter((summary) => summary.source === 'tracking');
  const demoSummaries = (telemetry?.summaries ?? []).filter((summary) => summary.source === 'demo');
  const visibleSummaries = isTrackingMode ? trackingSummaries : demoSummaries;
  const lastRun = systemMode?.last_tracking_run_at ?? automationRuns[0]?.completed_at ?? null;
  const prometheusHealth = prometheus?.health;
  const prometheusTargets = prometheus?.target_summary;
  const prometheusNode = prometheus?.node_summary;
  const lokiHealth = loki?.health;
  const lokiSources = loki?.log_source_summary;
  const lokiAuth = loki?.auth_failure_summary;
  const lokiServiceErrors = loki?.service_error_summary;
  const activeAlertsCount = telemetry?.overview_aggregates.active_alerts_count ?? alerts.filter((alert) => alert.status === 'active').length;
  const criticalSignalsCount = telemetry?.overview_aggregates.critical_signals_count ?? signals.filter((signal) => signal.severity === 'critical').length;
  const degradedServicesCount = telemetry?.overview_aggregates.degraded_services_count ?? serviceHealth.filter((service) => service.status === 'degraded').length;
  const telemetryHealth = telemetry?.overview_aggregates.telemetry_source_health_summary;
  const healthyTelemetrySources = telemetryHealth?.healthy ?? telemetrySourceHealth.filter((source) => source.status === 'healthy').length;
  const totalTelemetrySources = telemetryHealth?.total ?? telemetrySourceHealth.length;
  const highRiskVulnerabilityMatches = vulnerabilityMatches.filter((finding) => finding.score >= 70).length;

  const handleTrackingCycle = async () => {
    setRunningTracking(true);
    setTrackingError(null);
    try {
      await runTrackingCycle(selectedEnvironment.environment_id);
      onDataChanged();
    } catch (errorValue) {
      setTrackingError(errorValue instanceof Error ? errorValue.message : 'Unable to run tracking cycle');
    } finally {
      setRunningTracking(false);
    }
  };

  const riskyAssetColumns: DataColumn<RiskByAsset>[] = [
    { key: 'asset', label: 'Asset', render: (asset) => <span className="theme-text-primary font-medium">{asset.asset_name}</span> },
    { key: 'risk', label: 'Risk Score', render: (asset) => <StatusBadge label={String(asset.aggregate_score)} tone={asset.aggregate_score >= 85 ? 'red' : 'purple'} /> },
    { key: 'open', label: 'Open', render: (asset) => asset.open_findings },
    { key: 'critical', label: 'Critical', render: (asset) => asset.critical_count },
    { key: 'high', label: 'High', render: (asset) => asset.high_count },
  ];
  const findingColumns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Finding', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'asset', label: 'Asset', render: (finding) => assetNames[finding.asset_id] ?? finding.asset_id },
    { key: 'score', label: 'Risk Score', render: (finding) => <StatusBadge label={String(finding.score)} tone={finding.score >= 85 ? 'red' : finding.score >= 60 ? 'purple' : 'cyan'} /> },
    { key: 'severity', label: 'Severity', render: (finding) => <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} /> },
    { key: 'updated', label: 'Updated', render: (finding) => formatDate(finding.updated_at) },
  ];

  return (
    <div className="space-y-6">
      {(error || trackingError) && <div className="theme-error rounded-2xl p-4 text-sm">{error ?? trackingError}</div>}

      <Panel
        title={selectedEnvironment.name}
        eyebrow="Selected Environment"
        action={
          <button
            type="button"
            onClick={handleTrackingCycle}
            disabled={runningTracking}
            className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
          >
            {runningTracking ? 'Running...' : 'Run Tracking Cycle'}
          </button>
        }
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <StatusBadge label={selectedEnvironment.type} tone="cyan" />
            <StatusBadge label={isTrackingMode ? 'Tracking Mode' : 'Preview Mode'} tone={isTrackingMode ? 'cyan' : 'purple'} />
            <p className="theme-text-muted text-sm">
              Last tracking run: <span className="theme-text-secondary">{lastRun ? formatDate(lastRun) : 'never'}</span>
            </p>
          </div>
          <p className="theme-text-faint text-sm">
            {selectedEnvironment.description || (isTrackingMode ? 'Tracking data is active for posture views.' : 'Run a tracking cycle to populate posture data.')}
          </p>
        </div>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Active Alerts"
          value={postureLoading ? '...' : activeAlertsCount}
          caption="SOC and NOC alerts"
          accent={activeAlertsCount > 0 ? 'pink' : 'green'}
        />
        <MetricCard
          title="Critical Signals"
          value={postureLoading ? '...' : criticalSignalsCount}
          caption="High-priority SOC signal queue"
          accent={criticalSignalsCount > 0 ? 'pink' : 'green'}
        />
        <MetricCard
          title="Degraded Services"
          value={postureLoading ? '...' : degradedServicesCount}
          caption="NOC health monitoring"
          accent={degradedServicesCount > 0 ? 'purple' : 'green'}
        />
        <MetricCard
          title="Telemetry Source Health"
          value={postureLoading ? '...' : `${healthyTelemetrySources}/${totalTelemetrySources}`}
          caption="Healthy / total sources"
          accent={healthyTelemetrySources === totalTelemetrySources ? 'green' : 'purple'}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Matched Vulnerabilities"
          value={postureLoading ? '...' : vulnerabilityMatches.length}
          caption={`${highRiskVulnerabilityMatches} high-risk inventory match(es)`}
          accent={highRiskVulnerabilityMatches > 0 ? 'pink' : 'green'}
        />
        <MetricCard
          title="Prometheus Status"
          value={postureLoading ? '...' : prometheusHealth?.status ?? 'unknown'}
          caption={prometheusHealth?.enabled ? 'Read-only connector' : 'Connector disabled'}
          accent={prometheusHealth?.healthy ? 'green' : prometheusHealth?.enabled ? 'pink' : 'purple'}
        />
        <MetricCard
          title="Monitoring Coverage"
          value={postureLoading ? '...' : prometheusTargets?.active_target_count ?? 0}
          caption="Active scrape targets"
          accent="cyan"
        />
        <MetricCard
          title="Target Health"
          value={postureLoading ? '...' : `${prometheusTargets?.up_target_count ?? 0}/${prometheusTargets?.down_target_count ?? 0}`}
          caption="Up / down targets"
          accent={(prometheusTargets?.down_target_count ?? 0) > 0 ? 'pink' : 'green'}
        />
        <MetricCard
          title="Telemetry Ingestion"
          value={postureLoading ? '...' : prometheusNode?.node_exporter_present ? 'Node' : 'Limited'}
          caption={prometheusNode?.node_exporter_present ? `${prometheusNode.node_exporter_up_count} node exporter target(s)` : 'Node exporter not detected'}
          accent={prometheusNode?.node_exporter_present ? 'green' : 'purple'}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Loki Status"
          value={postureLoading ? '...' : lokiHealth?.status ?? 'unknown'}
          caption={lokiHealth?.enabled ? 'Log Ingestion read-only' : 'Log Ingestion disabled'}
          accent={lokiHealth?.healthy ? 'green' : lokiHealth?.enabled ? 'pink' : 'purple'}
        />
        <MetricCard
          title="Log Coverage"
          value={postureLoading ? '...' : lokiSources?.source_count ?? 0}
          caption={(lokiSources?.missing_sources.length ?? 0) > 0 ? `${lokiSources?.missing_sources.length ?? 0} expected source(s) missing` : 'Expected sources covered'}
          accent={(lokiSources?.missing_sources.length ?? 0) > 0 ? 'pink' : 'cyan'}
        />
        <MetricCard
          title="Authentication Signals"
          value={postureLoading ? '...' : lokiAuth?.event_count ?? 0}
          caption={lokiAuth?.status ? `${lokiAuth.status} across ${lokiAuth.source_count} source(s)` : 'No authentication signals loaded'}
          accent={(lokiAuth?.event_count ?? 0) >= 5 ? 'pink' : 'green'}
        />
        <MetricCard
          title="Service Error Signals"
          value={postureLoading ? '...' : lokiServiceErrors?.event_count ?? 0}
          caption={lokiServiceErrors?.status ? `${lokiServiceErrors.status} across ${lokiServiceErrors.source_count} source(s)` : 'No service error signals loaded'}
          accent={(lokiServiceErrors?.event_count ?? 0) >= 10 ? 'pink' : 'green'}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Total Assets" value={postureLoading ? '...' : assets.length} caption="Tracked homelab systems" accent="cyan" />
        <MetricCard title="Open Findings" value={postureLoading ? '...' : openFindings.length} caption="Posture items needing attention" accent="purple" />
        <MetricCard title="Critical Findings" value={postureLoading ? '...' : criticalFindings.length} caption="Highest priority exposure" accent="pink" />
        <MetricCard title="Completed Remediations" value={postureLoading ? '...' : completedRemediations.length} caption="Verified defensive work" accent="green" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel title="Findings by Severity" eyebrow="Posture">
          {postureLoading ? (
            <div className="theme-text-faint py-14 text-center text-sm">Loading severity summary...</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={severityData} margin={{ top: 10, right: 18, left: -18, bottom: 0 }}>
                <XAxis dataKey="name" stroke="var(--text-faint)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-faint)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip cursor={{ fill: 'color-mix(in srgb, var(--accent-purple) 8%, transparent)' }} content={<ChartTooltip />} />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {severityData.map((item) => (
                    <Cell key={item.name} fill={severityColors[item.name as FindingSeverity]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Panel>

        <Panel title="Findings by Category" eyebrow="Exposure">
          {postureLoading ? (
            <div className="theme-text-faint py-14 text-center text-sm">Loading category summary...</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={categoryData(findings)} dataKey="value" nameKey="name" innerRadius="58%" outerRadius="86%" paddingAngle={2}>
                  {categoryData(findings).map((item, index) => (
                    <Cell key={item.name} fill={categoryColors[index % categoryColors.length]} />
                  ))}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="Risky Assets" eyebrow="Risk by Asset">
          <DataTable columns={riskyAssetColumns} rows={visibleRiskyAssets} getRowKey={(asset) => asset.asset_id} emptyText="No risky assets returned by the API." />
        </Panel>
        <Panel title="Prioritized Findings" eyebrow="Top Open Findings">
          <DataTable columns={findingColumns} rows={topFindings.slice(0, 6)} getRowKey={(finding) => finding.id} emptyText="No open findings returned by the API." />
        </Panel>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.7fr_1.3fr]">
        <Panel title="Remediation Progress" eyebrow="Verification">
          <div className="space-y-5">
            <div>
              <div className="flex items-end justify-between">
                <p className="theme-text-primary text-5xl font-semibold">{postureLoading ? '...' : `${progress}%`}</p>
                <p className="theme-text-muted text-sm">{completedRemediations.length} of {remediations.length} completed</p>
              </div>
              <div className="theme-inset mt-5 h-3 overflow-hidden rounded-full">
                <div className="h-full rounded-full bg-gradient-to-r from-fuchsia-400 to-cyan-300" style={{ width: `${progress}%` }} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Plans</p>
                <p className="theme-text-primary mt-2 text-2xl font-semibold">{loading ? '...' : plans.length}</p>
              </div>
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Executions</p>
                <p className="theme-text-primary mt-2 text-2xl font-semibold">{loading ? '...' : executions.length}</p>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Telemetry Summary" eyebrow="Runtime, Network, Infrastructure">
          {postureLoading ? (
            <div className="theme-text-faint py-14 text-center text-sm">Loading telemetry summaries...</div>
          ) : isTrackingMode && visibleSummaries.length === 0 ? (
            <div className="py-14 text-center">
              <p className="theme-text-primary text-sm font-semibold">No live telemetry connected</p>
              <p className="theme-text-faint mt-2 text-sm">Run a tracking cycle or connect approved sources</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              {visibleSummaries.map((summary) => (
                <div key={summary.id} className="theme-inset rounded-2xl border p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="theme-text-primary text-sm font-semibold">{summary.source_name}</p>
                      <p className="theme-text-faint mt-1 text-xs">{summary.source_type}</p>
                    </div>
                    <StatusBadge label={summary.source === 'tracking' ? 'Tracking' : 'Preview'} tone={summary.source === 'tracking' ? 'cyan' : 'purple'} />
                  </div>
                  <p className="theme-text-primary mt-5 text-3xl font-semibold">{summary.event_count.toLocaleString()}</p>
                  <p className="theme-text-faint mt-1 text-xs">{summary.asset_count} assets, {summary.health_status}, updated {formatDate(summary.updated_at)}</p>
                  <ul className="mt-4 space-y-2">
                    {summary.notes.map((note) => (
                      <li key={note} className="theme-text-muted text-xs leading-5">
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
              {visibleSummaries.length === 0 && <div className="theme-text-faint py-14 text-center text-sm md:col-span-3">No live telemetry connected</div>}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
