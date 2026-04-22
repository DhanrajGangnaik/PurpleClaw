import { useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { runTrackingCycle } from '../services/api';
import type { AutomationRun, PrometheusSummary, SystemMode } from '../types/api';
import { formatDate } from '../utils';

interface AutomationProps {
  mode: SystemMode | null;
  runs: AutomationRun[];
  selectedEnvironmentId: string;
  prometheus: PrometheusSummary | null;
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

export function Automation({ mode, runs, selectedEnvironmentId, prometheus, loading, error, onDataChanged }: AutomationProps) {
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const latest = runs[0] ?? null;
  const columns: DataColumn<AutomationRun>[] = [
    { key: 'run_id', label: 'Run', render: (run) => <span className="font-mono text-[var(--accent-cyan)]">{run.run_id}</span> },
    { key: 'status', label: 'Status', render: (run) => <StatusBadge label={run.status} tone="cyan" /> },
    { key: 'assets', label: 'Assets', render: (run) => run.assets_discovered },
    { key: 'findings', label: 'Findings', render: (run) => run.findings_created },
    { key: 'score', label: 'Score', render: (run) => <StatusBadge label={String(run.posture_score)} tone={run.posture_score >= 70 ? 'green' : run.posture_score >= 40 ? 'purple' : 'red'} /> },
    { key: 'completed', label: 'Completed', render: (run) => formatDate(run.completed_at ?? undefined) },
  ];

  const handleRun = async () => {
    setRunning(true);
    setRunError(null);
    try {
      await runTrackingCycle(selectedEnvironmentId);
      onDataChanged();
    } catch (errorValue) {
      setRunError(errorValue instanceof Error ? errorValue.message : 'Unable to run tracking cycle');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {(error || runError) && <div className="theme-error rounded-2xl p-4 text-sm">{error ?? runError}</div>}

      <Panel
        title="Automation Control"
        eyebrow="Defensive Tracking"
        action={
          <button
            type="button"
            onClick={handleRun}
            disabled={running}
            className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60"
          >
            {running ? 'Running...' : 'Run Tracking Cycle'}
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Current Mode" value={mode?.mode === 'tracking' ? 'Tracking' : 'Preview'} caption={mode?.tracking_enabled ? 'Tracking enabled' : 'Run a tracking cycle to populate posture data'} accent={mode?.mode === 'tracking' ? 'cyan' : 'purple'} />
          <MetricCard title="Discovered Assets" value={loading ? '...' : latest?.assets_discovered ?? 0} caption="From recent automation run" accent="cyan" />
          <MetricCard title="Findings Created" value={loading ? '...' : latest?.findings_created ?? 0} caption="Derived defensively" accent="pink" />
          <MetricCard title="Posture Score" value={loading ? '...' : latest?.posture_score ?? 0} caption="Latest tracking cycle" accent="green" />
        </div>
      </Panel>

      <Panel title="Prometheus Status" eyebrow="Telemetry Ingestion">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Connector"
            value={loading ? '...' : prometheus?.health.status ?? 'unknown'}
            caption={prometheus?.config.enabled ? 'Read-only Prometheus API' : 'Disabled for this environment'}
            accent={prometheus?.health.healthy ? 'green' : prometheus?.config.enabled ? 'pink' : 'purple'}
          />
          <MetricCard
            title="Monitoring Coverage"
            value={loading ? '...' : prometheus?.target_summary.active_target_count ?? 0}
            caption="Active scrape targets"
            accent="cyan"
          />
          <MetricCard
            title="Target Health"
            value={loading ? '...' : `${prometheus?.target_summary.up_target_count ?? 0}/${prometheus?.target_summary.down_target_count ?? 0}`}
            caption="Up / down target summary"
            accent={(prometheus?.target_summary.down_target_count ?? 0) > 0 ? 'pink' : 'green'}
          />
          <MetricCard
            title="Node Metrics"
            value={loading ? '...' : prometheus?.node_summary.node_exporter_present ? 'Available' : 'Missing'}
            caption={prometheus?.node_summary.node_exporter_present ? 'CPU, memory, disk, network when exposed' : 'Node exporter not detected'}
            accent={prometheus?.node_summary.node_exporter_present ? 'green' : 'purple'}
          />
        </div>
      </Panel>

      <Panel title="Recent Automation Runs" eyebrow="Automation History">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading automation runs from PurpleClaw...</div>
        ) : (
          <DataTable
            columns={columns}
            rows={runs}
            getRowKey={(run) => run.run_id}
            emptyText="No automation runs available yet. Run a tracking cycle to populate posture data."
          />
        )}
      </Panel>
    </div>
  );
}
