import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnvironmentSwitcher } from '../components/EnvironmentSwitcher';
import { MetricCard } from '../components/MetricCard';
import { StatusBadge } from '../components/StatusBadge';
import type {
  Alert,
  AutomationRun,
  DashboardConfig,
  ManagedEnvironment,
  RegisteredDataSource,
  Report,
  ScanDetail,
  SecuritySignal,
} from '../types/api';
import { formatDate } from '../utils';

interface HomeProps {
  environments: ManagedEnvironment[];
  selectedEnvironment: ManagedEnvironment | null;
  selectedEnvironmentId: string;
  dashboards: DashboardConfig[];
  alerts: Alert[];
  scans: ScanDetail[];
  reports: Report[];
  datasources: RegisteredDataSource[];
  automationRuns: AutomationRun[];
  signals: SecuritySignal[];
  postureScore: number;
  loading: boolean;
  onEnvironmentChange: (environmentId: string) => void;
  onCreateEnvironmentRequest: () => void;
  onManageEnvironmentRequest: () => void;
}

type MetricAccent = 'cyan' | 'purple' | 'pink' | 'green' | 'amber';

interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  tone: 'cyan' | 'purple' | 'red' | 'green' | 'amber' | 'slate';
}

const quickActions = [
  { path: '/dashboards', label: 'Dashboards', description: 'View operational dashboards', color: '#008FEC' },
  { path: '/alerts', label: 'Alerts', description: 'Triage active alerts', color: '#FC4D64' },
  { path: '/scans', label: 'Run Scans', description: 'Execute controlled assessments', color: '#9013FE' },
  { path: '/reports', label: 'Reports', description: 'Generate and download reports', color: '#3EBD41' },
];

const navigationCards = [
  { path: '/datasources', label: 'Data Sources', description: 'Connector health and ingestion jobs' },
  { path: '/signals', label: 'Signals', description: 'Correlation-ready security signals' },
  { path: '/scheduler', label: 'Scheduler', description: 'Platform health and automation jobs' },
  { path: '/automation', label: 'Automation', description: 'Safe tracking cycles and posture sync' },
  { path: '/settings', label: 'Settings', description: 'Environments and workspace setup' },
  { path: '/remediation', label: 'Remediation', description: 'Remediation tasks mapped to findings' },
];

export function Home({
  environments,
  selectedEnvironment,
  selectedEnvironmentId,
  dashboards,
  alerts,
  scans,
  reports,
  datasources,
  automationRuns,
  signals,
  postureScore,
  loading,
  onEnvironmentChange,
  onCreateEnvironmentRequest,
  onManageEnvironmentRequest,
}: HomeProps) {
  const navigate = useNavigate();
  const environmentType = selectedEnvironment?.type ?? 'environment';

  const kpis = useMemo(() => {
    const activeAlerts = alerts.filter((a) => a.status === 'active').length;
    const connectedSources = datasources.filter((d) => d.environment_id === selectedEnvironmentId && d.status === 'enabled').length;
    const criticalSignals = signals.filter((s) => s.severity === 'critical').length;

    return [
      {
        title: 'Posture Score',
        value: loading ? '—' : `${postureScore}`,
        caption: `${environmentType} environment health`,
        accent: (postureScore >= 80 ? 'green' : postureScore >= 60 ? 'cyan' : 'pink') as MetricAccent,
      },
      {
        title: 'Active Alerts',
        value: loading ? '—' : activeAlerts,
        caption: 'Live issues needing review',
        accent: (activeAlerts > 0 ? 'pink' : 'green') as MetricAccent,
      },
      {
        title: 'Connected Sources',
        value: loading ? '—' : connectedSources,
        caption: 'Enabled data pipelines',
        accent: 'cyan' as MetricAccent,
      },
      {
        title: 'Critical Signals',
        value: loading ? '—' : criticalSignals,
        caption: 'Detection queue requiring action',
        accent: (criticalSignals > 0 ? 'pink' : 'green') as MetricAccent,
      },
    ];
  }, [alerts, datasources, environmentType, loading, postureScore, selectedEnvironmentId, signals]);

  const recentActivity = useMemo<ActivityItem[]>(() => {
    const scanItems = scans.slice(0, 3).map((scan) => ({
      id: `scan-${scan.request.scan_id}`,
      title: `Scan: ${scan.request.target}`,
      detail: scan.result?.status ?? scan.request.status,
      timestamp: scan.result?.completed_at ?? scan.result?.started_at ?? scan.request.requested_at,
      tone: ((scan.result?.status ?? scan.request.status) === 'completed' ? 'green' : 'purple') as ActivityItem['tone'],
    }));
    const reportItems = reports.slice(0, 2).map((report) => ({
      id: `report-${report.report_id}`,
      title: report.title,
      detail: `${report.generated_from} report`,
      timestamp: report.generated_at,
      tone: 'cyan' as const,
    }));
    const runItems = automationRuns.slice(0, 2).map((run) => ({
      id: `run-${run.run_id}`,
      title: `Automation: ${run.status}`,
      detail: `${run.findings_created} findings`,
      timestamp: run.completed_at ?? run.started_at,
      tone: 'slate' as const,
    }));

    return [...scanItems, ...reportItems, ...runItems]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 6);
  }, [automationRuns, reports, scans]);

  const envDashboards = dashboards.filter((d) => d.environment_id === selectedEnvironmentId).length;
  const envScans = scans.filter((s) => s.request.environment_id === selectedEnvironmentId).length;
  const environmentStatusTone = selectedEnvironment?.status === 'active' ? 'green' : 'slate';

  if (!selectedEnvironment) {
    return (
      <div className="space-y-6">
        <section className="workspace-panel p-6">
          <p className="workspace-eyebrow">Workspace Summary</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
            No environment selected
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
            No environments yet. Create one to begin.
          </p>
          <div className="mt-6">
            <button type="button" onClick={onCreateEnvironmentRequest} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold">
              Create Environment
            </button>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="workspace-panel p-5 sm:p-6">
        <div className="grid gap-6 xl:grid-cols-[1.5fr,0.9fr]">
          <div>
            <p className="workspace-eyebrow">Workspace Summary</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>
              {selectedEnvironment.name}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
              {selectedEnvironment.description || 'No description provided.'}
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-2">
              <StatusBadge label={selectedEnvironment.type} tone="purple" />
              <StatusBadge label={selectedEnvironment.status} tone={environmentStatusTone} />
              <StatusBadge label={`${datasources.length} data sources`} tone="cyan" />
            </div>
            <div className="mt-6">
              <EnvironmentSwitcher
                environments={environments}
                selectedEnvironmentId={selectedEnvironmentId}
                onEnvironmentChange={onEnvironmentChange}
                onManageEnvironmentRequest={onManageEnvironmentRequest}
              />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="workspace-stat">
              <p className="workspace-eyebrow">Coverage</p>
              <p className="mt-3 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>{envDashboards}</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Configured operational dashboards</p>
            </div>
            <div className="workspace-stat">
              <p className="workspace-eyebrow">Assessments</p>
              <p className="mt-3 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>{envScans}</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Recorded scan runs in this environment</p>
            </div>
            <div className="workspace-stat">
              <p className="workspace-eyebrow">Reporting</p>
              <p className="mt-3 text-2xl font-semibold" style={{ color: 'var(--text-primary)' }}>{reports.length}</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Available generated reports</p>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi) => (
          <MetricCard key={kpi.title} title={kpi.title} value={kpi.value} caption={kpi.caption} accent={kpi.accent} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr,360px]">
        <div className="workspace-panel p-5 sm:p-6">
          <p className="workspace-eyebrow">Workflows</p>
          <h2 className="mt-2 text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Quick Actions</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {quickActions.map((action) => (
              <button
                key={action.path}
                type="button"
                onClick={() => navigate(action.path)}
                className="workspace-subpanel flex items-start gap-4 p-4 text-left transition-all duration-150 hover:-translate-y-px"
              >
                <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border" style={{ borderColor: 'var(--border)', background: 'var(--surface-overlay)' }}>
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: action.color }} />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{action.label}</p>
                  <p className="mt-1 text-xs leading-5" style={{ color: 'var(--text-muted)' }}>{action.description}</p>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="workspace-panel p-5 sm:p-6">
          <p className="workspace-eyebrow">Timeline</p>
          <h2 className="mt-2 text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Recent Activity</h2>
          <div className="mt-4 space-y-2">
            {recentActivity.length === 0 ? (
              <p className="py-8 text-center text-sm" style={{ color: 'var(--text-disabled)' }}>No recent activity.</p>
            ) : (
              recentActivity.map((item) => (
                <div key={item.id} className="workspace-subpanel flex items-start justify-between gap-4 px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>{item.title}</p>
                    <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--text-muted)' }}>{item.detail}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <StatusBadge label={item.tone} tone={item.tone} />
                    <p className="text-[11px] mt-1" style={{ color: 'var(--text-disabled)' }}>
                      {formatDate(item.timestamp)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="workspace-panel p-5 sm:p-6">
        <p className="workspace-eyebrow">Navigate</p>
        <h2 className="mt-2 text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>Platform Areas</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {navigationCards.map((card) => (
            <button
              key={card.path}
              type="button"
              onClick={() => navigate(card.path)}
              className="workspace-subpanel p-4 text-left transition-all duration-150 hover:-translate-y-px"
            >
              <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{card.label}</p>
              <p className="mt-1 text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{card.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
