import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Finding, RemediationTask } from '../types/api';
import { formatDate } from '../utils';

interface RemediationProps {
  findings: Finding[];
  remediations: RemediationTask[];
  loading: boolean;
  error: string | null;
}

function taskTone(status: string) {
  if (status === 'completed') {
    return 'green';
  }
  if (status === 'blocked') {
    return 'red';
  }
  if (status === 'in-progress') {
    return 'cyan';
  }
  return 'purple';
}

export function Remediation({ findings, remediations, loading, error }: RemediationProps) {
  const [params] = useSearchParams();
  const findingId = params.get('finding');
  const [selectedTask, setSelectedTask] = useState<RemediationTask | null>(null);
  const findingTitles = useMemo(() => Object.fromEntries(findings.map((finding) => [finding.id, finding.title])), [findings]);
  const filteredTasks = findingId ? remediations.filter((task) => task.finding_id === findingId) : remediations;
  const activeTask = selectedTask && filteredTasks.some((task) => task.id === selectedTask.id) ? selectedTask : filteredTasks[0] ?? null;
  const columns: DataColumn<RemediationTask>[] = [
    { key: 'title', label: 'Task', render: (task) => <span className="theme-text-primary font-medium">{task.title}</span> },
    { key: 'finding', label: 'Finding', render: (task) => findingTitles[task.finding_id] ?? task.finding_id },
    { key: 'status', label: 'Status', render: (task) => <StatusBadge label={task.status} tone={taskTone(task.status)} /> },
    { key: 'owner', label: 'Owner', render: (task) => task.owner },
    { key: 'due', label: 'Due', render: (task) => formatDate(task.due_date) },
  ];

  return (
    <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
      <Panel
        title={findingId ? `Remediation for ${findingTitles[findingId] ?? findingId}` : 'Remediation Queue'}
        eyebrow={findingId ? 'Finding Remediation' : 'Remediation Work'}
      >
        {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading remediation tasks from PurpleClaw...</div>
        ) : (
          <DataTable
            columns={columns}
            rows={filteredTasks}
            getRowKey={(task) => task.id}
            emptyText="No remediation tasks matched this view."
            onRowClick={setSelectedTask}
          />
        )}
      </Panel>

      <Panel title="Remediation Detail" eyebrow="Verification">
        {activeTask ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4">
              <p className="theme-text-primary text-sm font-semibold">{activeTask.title}</p>
              <p className="theme-text-muted mt-2 text-sm">{findingTitles[activeTask.finding_id] ?? activeTask.finding_id}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Owner</p>
                <p className="theme-text-primary mt-2 text-lg font-semibold">{activeTask.owner}</p>
              </div>
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Status</p>
                <div className="mt-2">
                  <StatusBadge label={activeTask.status} tone={taskTone(activeTask.status)} />
                </div>
              </div>
            </div>
            <div>
              <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Steps</p>
              <ul className="mt-3 space-y-2">
                {activeTask.steps.map((step) => (
                  <li key={step} className="theme-inset rounded-xl border px-3 py-2 text-sm">
                    {step}
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-2xl border border-fuchsia-400/20 bg-fuchsia-400/10 p-4 text-sm theme-text-secondary">
              {activeTask.verification}
            </div>
          </div>
        ) : (
          <div className="theme-text-faint py-14 text-center text-sm">Select a remediation task to inspect verification detail.</div>
        )}
      </Panel>
    </div>
  );
}
