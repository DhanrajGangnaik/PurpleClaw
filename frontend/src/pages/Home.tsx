import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { EnvironmentSwitcher } from '../components/EnvironmentSwitcher';
import { MetricCard } from '../components/MetricCard';
import { Panel } from '../components/Panel';
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
  selectedEnvironment: ManagedEnvironment;
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

interface ActivityItem {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  tone: 'cyan' | 'purple' | 'red' | 'green';
}

type MetricAccent = 'cyan' | 'purple' | 'pink' | 'green';

const navigationCards = [
  { path: '/dashboards', title: 'Dashboards', description: 'Focused operational views for security posture and telemetry.' },
  { path: '/alerts', title: 'Alerts', description: 'Triage active alerts without the rest of the platform noise.' },
  { path: '/scans', title: 'Scans', description: 'Run and review controlled assessments for the active environment.' },
  { path: '/reports', title: 'Reports', description: 'Generate and download concise updates for stakeholders.' },
  { path: '/datasources', title: 'Data Sources', description: 'Check connector coverage, ingestion jobs, and source health.' },
  { path: '/settings', title: 'Settings', description: 'Manage environments and tune the workspace structure.' },
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

  const quickStats = useMemo(
    () => [
      {
        title: 'Posture Score',
        value: loading ? '...' : postureScore,
        caption: `${selectedEnvironment.type} environment health snapshot`,
        accent: (postureScore >= 80 ? 'green' : postureScore >= 60 ? 'cyan' : 'pink') as MetricAccent,
      },
      {
        title: 'Open Alerts',
        value: loading ? '...' : alerts.filter((alert) => alert.status === 'active').length,
        caption: 'Live issues needing review',
        accent: (alerts.some((alert) => alert.status === 'active') ? 'pink' : 'green') as MetricAccent,
      },
      {
        title: 'Connected Sources',
        value: loading ? '...' : datasources.filter((source) => source.environment_id === selectedEnvironmentId && source.status === 'enabled').length,
        caption: 'Enabled data pipelines',
        accent: 'cyan' as MetricAccent,
      },
      {
        title: 'Critical Signals',
        value: loading ? '...' : signals.filter((signal) => signal.severity === 'critical').length,
        caption: 'Detection queue requiring action',
        accent: (signals.some((signal) => signal.severity === 'critical') ? 'pink' : 'green') as MetricAccent,
      },
    ],
    [alerts, datasources, loading, postureScore, selectedEnvironment.type, selectedEnvironmentId, signals],
  );

  const recentActivity = useMemo<ActivityItem[]>(() => {
    const scanItems = scans.slice(0, 3).map((scan) => ({
      id: `scan-${scan.request.scan_id}`,
      title: `Scan ${scan.request.target}`,
      detail: `Status: ${scan.result?.status ?? scan.request.status}`,
      timestamp: scan.result?.completed_at ?? scan.result?.started_at ?? scan.request.requested_at,
      tone: (scan.result?.status ?? scan.request.status) === 'completed' ? ('green' as const) : ('purple' as const),
    }));
    const reportItems = reports.slice(0, 2).map((report) => ({
      id: `report-${report.report_id}`,
      title: report.title,
      detail: `${report.generated_from} report`,
      timestamp: report.generated_at,
      tone: 'cyan' as const,
    }));
    const automationItems = automationRuns.slice(0, 2).map((run) => ({
      id: `run-${run.run_id}`,
      title: `Automation ${run.status}`,
      detail: `${run.findings_created} findings created`,
      timestamp: run.completed_at ?? run.started_at,
      tone: 'purple' as const,
    }));

    return [...scanItems, ...reportItems, ...automationItems]
      .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
      .slice(0, 6);
  }, [automationRuns, reports, scans]);

  const quickActions = [
    { label: 'Open Dashboards', path: '/dashboards' },
    { label: 'Run Scans', path: '/scans' },
    { label: 'Review Alerts', path: '/alerts' },
    { label: 'Generate Reports', path: '/reports' },
  ];

  return (
    <div className="space-y-6">
      <Panel
        title={selectedEnvironment.name}
        eyebrow="Home"
        description={selectedEnvironment.description}
        action={<StatusBadge label={selectedEnvironment.status} tone={selectedEnvironment.status === 'active' ? 'cyan' : 'slate'} />}
      >
        <EnvironmentSwitcher
          environments={environments}
          selectedEnvironmentId={selectedEnvironmentId}
          onEnvironmentChange={onEnvironmentChange}
          onCreateEnvironmentRequest={onCreateEnvironmentRequest}
          onManageEnvironmentRequest={onManageEnvironmentRequest}
        />
      </Panel>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {quickStats.map((stat) => (
          <MetricCard key={stat.title} title={stat.title} value={stat.value} caption={stat.caption} accent={stat.accent} />
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <Panel title="Quick Actions" description="Move directly into the primary workflows for the active environment.">
          <div className="grid gap-3 sm:grid-cols-2">
            {quickActions.map((action) => (
              <button
                key={action.path}
                type="button"
                onClick={() => navigate(action.path)}
                className="theme-inset theme-text-primary rounded-2xl border px-4 py-4 text-left text-sm font-semibold transition hover:translate-y-[-1px] hover:bg-[var(--table-hover)]"
              >
                {action.label}
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="Recent Activity" description="The latest scans, reports, and automation events.">
          <div className="space-y-3">
            {recentActivity.map((item) => (
              <div key={item.id} className="theme-inset flex items-start justify-between gap-4 rounded-2xl border px-4 py-3">
                <div>
                  <p className="theme-text-primary text-sm font-semibold">{item.title}</p>
                  <p className="theme-text-muted mt-1 text-sm">{item.detail}</p>
                </div>
                <div className="text-right">
                  <StatusBadge label={item.tone} tone={item.tone} />
                  <p className="theme-text-faint mt-2 text-xs">{formatDate(item.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel title="Navigation" description="The main product areas are reduced to the views that matter most day to day.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {navigationCards.map((card) => (
            <button
              key={card.path}
              type="button"
              onClick={() => navigate(card.path)}
              className="theme-inset rounded-3xl border px-5 py-5 text-left transition hover:translate-y-[-2px] hover:bg-[var(--table-hover)]"
            >
              <p className="theme-text-primary text-base font-semibold">{card.title}</p>
              <p className="theme-text-muted mt-2 text-sm leading-6">{card.description}</p>
            </button>
          ))}
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-3">
        <Panel title="Dashboards" description="Keep the dashboard layer intentional and small.">
          <p className="theme-text-primary text-3xl font-semibold">{dashboards.filter((dashboard) => dashboard.environment_id === selectedEnvironmentId).length}</p>
          <p className="theme-text-muted mt-2 text-sm">Configured views for this environment.</p>
        </Panel>
        <Panel title="Scans" description="Assessments stay visible without taking over the landing page.">
          <p className="theme-text-primary text-3xl font-semibold">{scans.length}</p>
          <p className="theme-text-muted mt-2 text-sm">Recorded scan runs for the current environment.</p>
        </Panel>
        <Panel title="Reports" description="Keep reporting close to operations, not buried under analytics.">
          <p className="theme-text-primary text-3xl font-semibold">{reports.length}</p>
          <p className="theme-text-muted mt-2 text-sm">Generated reports ready for download or review.</p>
        </Panel>
      </div>
    </div>
  );
}
