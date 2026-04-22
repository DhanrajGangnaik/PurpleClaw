import { useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { createPlatformBackup, runScheduledIntelligence, runScheduledInventory, runScheduledTracking } from '../services/api';
import type { AutomationRun, IntelligenceUpdateRun, PlatformBackup, PlatformHealth, SchedulerJobStatus, SchedulerStatus } from '../types/api';
import { formatDate } from '../utils';

interface SchedulerProps {
  selectedEnvironmentId: string;
  status: SchedulerStatus | null;
  platformHealth: PlatformHealth | null;
  platformBackups: PlatformBackup[];
  automationRuns: AutomationRun[];
  intelligenceRuns: IntelligenceUpdateRun[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

type JobName = 'tracking' | 'intelligence' | 'inventory';

export function Scheduler({ selectedEnvironmentId, status, platformHealth, platformBackups, automationRuns, intelligenceRuns, loading, error, onDataChanged }: SchedulerProps) {
  const [runningJob, setRunningJob] = useState<JobName | null>(null);
  const [backingUp, setBackingUp] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const jobs = status?.jobs ?? null;
  const rows = jobs
    ? (Object.entries(jobs) as [JobName, SchedulerJobStatus][]).map(([name, job]) => ({ name, ...job }))
    : [];
  const columns: DataColumn<(typeof rows)[number]>[] = [
    { key: 'name', label: 'Job', render: (job) => <span className="theme-text-primary font-medium">{job.name}</span> },
    { key: 'status', label: 'Status', render: (job) => <StatusBadge label={job.last_status} tone={job.last_status === 'completed' ? 'green' : 'purple'} /> },
    { key: 'last', label: 'Last Run', render: (job) => formatDate(job.last_run_at ?? undefined) },
    { key: 'next', label: 'Next Estimate', render: (job) => formatDate(job.next_run_at ?? undefined) },
    { key: 'interval', label: 'Interval', render: (job) => `${job.interval_minutes} min` },
    {
      key: 'action',
      label: 'Run Now',
      render: (job) => (
        <button type="button" onClick={() => handleRun(job.name)} disabled={runningJob === job.name} className="theme-button-secondary rounded-2xl px-3 py-1.5 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-60">
          {runningJob === job.name ? 'Running...' : 'Run'}
        </button>
      ),
    },
  ];
  const backupColumns: DataColumn<PlatformBackup>[] = [
    { key: 'name', label: 'Backup', render: (backup) => <span className="theme-text-primary font-mono text-xs">{backup.filename}</span> },
    { key: 'size', label: 'Size', render: (backup) => formatBytes(backup.size_bytes) },
    { key: 'created', label: 'Created', render: (backup) => formatDate(backup.created_at) },
  ];

  const handleRun = async (jobName: JobName) => {
    setRunningJob(jobName);
    setRunError(null);
    try {
      if (jobName === 'tracking') {
        await runScheduledTracking(selectedEnvironmentId);
      } else if (jobName === 'intelligence') {
        await runScheduledIntelligence(selectedEnvironmentId);
      } else {
        await runScheduledInventory(selectedEnvironmentId);
      }
      onDataChanged();
    } catch (errorValue) {
      setRunError(errorValue instanceof Error ? errorValue.message : 'Unable to run scheduled job');
    } finally {
      setRunningJob(null);
    }
  };

  const handleBackup = async () => {
    setBackingUp(true);
    setRunError(null);
    try {
      await createPlatformBackup();
      onDataChanged();
    } catch (errorValue) {
      setRunError(errorValue instanceof Error ? errorValue.message : 'Unable to create backup');
    } finally {
      setBackingUp(false);
    }
  };

  return (
    <div className="space-y-6">
      {(error || runError) && <div className="theme-error rounded-2xl p-4 text-sm">{error ?? runError}</div>}
      <Panel title="Scheduler" eyebrow="Operations">
        <div className="grid gap-4 md:grid-cols-3">
          <MetricCard title="Scheduler Mode" value={loading ? '...' : status?.mode ?? 'unknown'} caption={status?.enabled ? 'Safe in-process automation' : 'Scheduler disabled'} accent="cyan" />
          <MetricCard title="Automation Runs" value={loading ? '...' : automationRuns.length} caption="Tracking and inventory history" accent="purple" />
          <MetricCard title="Intelligence Runs" value={loading ? '...' : intelligenceRuns.length} caption="Curated update history" accent="green" />
        </div>
      </Panel>

      <Panel
        title="Platform Database"
        eyebrow="Persistence Health"
        action={
          <button type="button" onClick={handleBackup} disabled={backingUp || platformHealth?.backend !== 'sqlite'} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60">
            {backingUp ? 'Backing up...' : 'Backup Now'}
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="DB Backend" value={loading ? '...' : platformHealth?.backend ?? 'unknown'} caption={platformHealth?.database_path ?? 'Advanced database backend'} accent="cyan" />
          <MetricCard title="Connection" value={loading ? '...' : platformHealth?.connection_status ?? 'unknown'} caption={platformHealth?.writable ? 'Writable' : 'Read-only or unavailable'} accent={platformHealth?.connection_status === 'connected' ? 'green' : 'pink'} />
          <MetricCard title="DB Size" value={loading ? '...' : formatBytes(platformHealth?.metrics.database_size_bytes ?? 0)} caption="Embedded database file" accent="purple" />
          <MetricCard title="Last Backup" value={loading ? '...' : platformBackups[0] ? 'Available' : 'None'} caption={platformBackups[0]?.created_at ? formatDate(platformBackups[0].created_at) : 'No backup yet'} accent="green" />
        </div>
      </Panel>

      <Panel title="Scheduled Jobs" eyebrow="Run Controls">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading scheduler status...</div>
        ) : (
          <DataTable columns={columns} rows={rows} getRowKey={(job) => job.name} emptyText="No scheduler jobs returned by the API." />
        )}
      </Panel>

      <Panel title="Backups" eyebrow="Embedded SQLite">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading backups...</div>
        ) : (
          <DataTable columns={backupColumns} rows={platformBackups} getRowKey={(backup) => backup.filename} emptyText="No backups available yet." />
        )}
      </Panel>

      <Panel title="Run History" eyebrow="Recent Automation">
        <div className="grid gap-4 md:grid-cols-2">
          {automationRuns.slice(0, 6).map((run) => (
            <div key={run.run_id} className="theme-inset rounded-2xl border p-4">
              <p className="theme-text-primary font-semibold">{run.status}</p>
              <p className="theme-text-faint mt-1 text-xs">{run.run_id} completed {formatDate(run.completed_at ?? undefined)}</p>
            </div>
          ))}
          {intelligenceRuns.slice(0, 6).map((run) => (
            <div key={run.run_id} className="theme-inset rounded-2xl border p-4">
              <p className="theme-text-primary font-semibold">intelligence update</p>
              <p className="theme-text-faint mt-1 text-xs">{run.run_id} reprioritized {run.findings_reprioritized} finding(s)</p>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function formatBytes(value: number | null | undefined) {
  const bytes = value ?? 0;
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
