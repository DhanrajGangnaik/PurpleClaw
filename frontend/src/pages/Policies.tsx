import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Policy } from '../types/api';
import { formatDate } from '../utils';

interface PoliciesProps {
  policies: Policy[];
  loading: boolean;
  error: string | null;
}

export function Policies({ policies, loading, error }: PoliciesProps) {
  const columns: DataColumn<Policy>[] = [
    { key: 'name', label: 'Policy', render: (policy) => <span className="theme-text-primary font-medium">{policy.name}</span> },
    { key: 'domain', label: 'Domain', render: (policy) => <StatusBadge label={policy.domain} tone="cyan" /> },
    { key: 'status', label: 'Status', render: (policy) => <StatusBadge label={policy.status} tone={policy.status === 'active' ? 'green' : 'purple'} /> },
    { key: 'coverage', label: 'Coverage', render: (policy) => `${policy.coverage}%` },
    { key: 'requirements', label: 'Requirements', render: (policy) => policy.requirements.length },
    { key: 'reviewed', label: 'Reviewed', render: (policy) => formatDate(policy.last_reviewed) },
  ];

  return (
    <Panel title="Policy Library" eyebrow="Control Coverage">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading policies from PurpleClaw...</div>
      ) : (
        <DataTable columns={columns} rows={policies} getRowKey={(policy) => policy.id} emptyText="No policies returned by the API." />
      )}
    </Panel>
  );
}
