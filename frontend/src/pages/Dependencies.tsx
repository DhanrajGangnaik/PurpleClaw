import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { DependencyStatus } from '../types/api';

interface DependenciesProps {
  dependencies: DependencyStatus[];
  loading: boolean;
  error: string | null;
}

function statusTone(status: string) {
  if (status === 'healthy') {
    return 'green';
  }
  if (status === 'degraded') {
    return 'purple';
  }
  return 'red';
}

export function Dependencies({ dependencies, loading, error }: DependenciesProps) {
  const columns: DataColumn<DependencyStatus>[] = [
    { key: 'name', label: 'Dependency Name', render: (dependency) => <span className="theme-text-primary font-medium">{dependency.name}</span> },
    { key: 'type', label: 'Type', render: (dependency) => <StatusBadge label={dependency.type} tone="cyan" /> },
    { key: 'status', label: 'Status', render: (dependency) => <StatusBadge label={dependency.status} tone={statusTone(dependency.status)} /> },
    { key: 'notes', label: 'Notes', render: (dependency) => dependency.notes },
  ];

  return (
    <Panel title="Dependencies" eyebrow="Platform Health">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading dependencies from PurpleClaw...</div>
      ) : (
        <DataTable columns={columns} rows={dependencies} getRowKey={(dependency) => dependency.dependency_id} emptyText="No dependencies returned by the API." />
      )}
    </Panel>
  );
}
