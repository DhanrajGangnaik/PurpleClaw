import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Alert, Asset, FindingSeverity } from '../types/api';
import { formatDate } from '../utils';

interface AlertsProps {
  alerts: Alert[];
  assets: Asset[];
  loading: boolean;
  error: string | null;
}

function severityTone(severity: FindingSeverity) {
  if (severity === 'critical' || severity === 'high') {
    return 'red';
  }
  if (severity === 'medium') {
    return 'purple';
  }
  return 'cyan';
}

export function Alerts({ alerts, assets, loading, error }: AlertsProps) {
  const assetNames = Object.fromEntries(assets.map((asset) => [asset.id, asset.name]));
  const columns: DataColumn<Alert>[] = [
    { key: 'title', label: 'Title', render: (alert) => <span className="theme-text-primary font-medium">{alert.title}</span> },
    { key: 'source', label: 'Source', render: (alert) => alert.source },
    { key: 'severity', label: 'Severity', render: (alert) => <StatusBadge label={alert.severity} tone={severityTone(alert.severity)} /> },
    { key: 'status', label: 'Status', render: (alert) => <StatusBadge label={alert.status} tone={alert.status === 'active' ? 'red' : 'purple'} /> },
    { key: 'asset', label: 'Asset', render: (alert) => (alert.asset_id ? assetNames[alert.asset_id] ?? alert.asset_id : 'Unmapped') },
    { key: 'started', label: 'Started At', render: (alert) => formatDate(alert.started_at) },
  ];

  return (
    <Panel title="Alerts" eyebrow="SOC and NOC">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading alerts from PurpleClaw...</div>
      ) : (
        <DataTable columns={columns} rows={alerts} getRowKey={(alert) => alert.alert_id} emptyText="No active alerts returned by the API." />
      )}
    </Panel>
  );
}
