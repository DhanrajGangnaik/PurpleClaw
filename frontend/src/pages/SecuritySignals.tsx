import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Asset, FindingSeverity, SecuritySignal } from '../types/api';
import { formatDate } from '../utils';

interface SecuritySignalsProps {
  signals: SecuritySignal[];
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

export function SecuritySignals({ signals, assets, loading, error }: SecuritySignalsProps) {
  const assetNames = Object.fromEntries(assets.map((asset) => [asset.id, asset.name]));
  const columns: DataColumn<SecuritySignal>[] = [
    { key: 'title', label: 'Title', render: (signal) => <span className="theme-text-primary font-medium">{signal.title}</span> },
    { key: 'category', label: 'Category', render: (signal) => <StatusBadge label={signal.category} tone="cyan" /> },
    { key: 'source', label: 'Source', render: (signal) => signal.source },
    { key: 'severity', label: 'Severity', render: (signal) => <StatusBadge label={signal.severity} tone={severityTone(signal.severity)} /> },
    { key: 'confidence', label: 'Confidence', render: (signal) => <StatusBadge label={signal.confidence} tone={signal.confidence === 'high' ? 'green' : 'purple'} /> },
    { key: 'asset', label: 'Asset', render: (signal) => (signal.asset_id ? assetNames[signal.asset_id] ?? signal.asset_id : 'Unmapped') },
    { key: 'detected', label: 'Detected At', render: (signal) => formatDate(signal.detected_at) },
  ];

  return (
    <Panel title="Security Signals" eyebrow="SOC Signal Aggregation">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading security signals from PurpleClaw...</div>
      ) : (
        <DataTable columns={columns} rows={signals} getRowKey={(signal) => signal.signal_id} emptyText="No security signals returned by the API." />
      )}
    </Panel>
  );
}
