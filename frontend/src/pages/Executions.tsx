import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { ExecutionResult } from '../types/api';
import { formatDate, shortId } from '../utils';

interface ExecutionsProps {
  executions: ExecutionResult[];
  loading: boolean;
  error: string | null;
}

export function Executions({ executions, loading, error }: ExecutionsProps) {
  const columns: DataColumn<ExecutionResult>[] = [
    { key: 'execution_id', label: 'Execution ID', render: (execution) => <span className="font-mono text-[var(--accent-cyan)]" title={execution.execution_id}>{shortId(execution.execution_id, 14)}</span> },
    { key: 'plan_id', label: 'Plan ID', render: (execution) => <span className="theme-text-primary font-mono">{execution.plan_id}</span> },
    { key: 'executor', label: 'Executor', render: (execution) => <StatusBadge label={execution.executor} tone="purple" /> },
    { key: 'status', label: 'Status', render: (execution) => <StatusBadge label={execution.status} tone="cyan" /> },
    { key: 'executed', label: 'Executed', render: (execution) => <StatusBadge label={String(execution.executed)} tone={execution.executed ? 'red' : 'green'} /> },
    { key: 'executed_at', label: 'Executed At', render: (execution) => formatDate(execution.executed_at) },
  ];

  return (
    <Panel title="Validation Results" eyebrow="Verification History">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading executions from PurpleClaw...</div>
      ) : (
        <DataTable
          columns={columns}
          rows={executions}
          getRowKey={(execution) => execution.execution_id}
          emptyText="No validation results available yet. Record a verification result from Validator."
        />
      )}
    </Panel>
  );
}
