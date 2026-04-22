import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Asset, Finding, FindingSeverity, InventoryRecord } from '../types/api';
import { formatDate } from '../utils';

interface InventoryProps {
  assets: Asset[];
  inventory: InventoryRecord[];
  vulnerabilityMatches: Finding[];
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

export function Inventory({ assets, inventory, vulnerabilityMatches, loading, error }: InventoryProps) {
  const assetNames = Object.fromEntries(assets.map((asset) => [asset.id, asset.name]));
  const inventoryColumns: DataColumn<InventoryRecord>[] = [
    { key: 'component', label: 'Component', render: (record) => <span className="theme-text-primary font-medium">{record.component_name}</span> },
    { key: 'type', label: 'Type', render: (record) => <StatusBadge label={record.component_type} tone="cyan" /> },
    { key: 'version', label: 'Version', render: (record) => record.version },
    { key: 'asset', label: 'Asset', render: (record) => assetNames[record.asset_id] ?? record.asset_id },
    { key: 'source', label: 'Source', render: (record) => <StatusBadge label={record.source} tone={record.source === 'tracking' ? 'purple' : 'slate'} /> },
    { key: 'detected', label: 'Detected', render: (record) => formatDate(record.detected_at) },
  ];
  const matchColumns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Matched Vulnerability', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'score', label: 'Risk Score', render: (finding) => <StatusBadge label={String(finding.score)} tone={finding.score >= 85 ? 'red' : finding.score >= 60 ? 'purple' : 'cyan'} /> },
    { key: 'severity', label: 'Severity', render: (finding) => <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} /> },
    { key: 'asset', label: 'Asset', render: (finding) => assetNames[finding.asset_id] ?? finding.asset_id },
    { key: 'component', label: 'Component', render: (finding) => finding.affected_component ?? 'Unknown component' },
    { key: 'recommendation', label: 'Recommendation', render: (finding) => finding.verification },
  ];

  return (
    <div className="space-y-6">
      <Panel title="Inventory" eyebrow="Packages and Services">
        {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading inventory from PurpleClaw...</div>
        ) : (
          <DataTable columns={inventoryColumns} rows={inventory} getRowKey={(record) => record.inventory_id} emptyText="No inventory records returned by the API." />
        )}
      </Panel>

      <Panel title="Matched Vulnerabilities" eyebrow="Seeded CVE Matching">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading vulnerability matches from PurpleClaw...</div>
        ) : (
          <DataTable columns={matchColumns} rows={vulnerabilityMatches} getRowKey={(finding) => finding.id} emptyText="No seeded CVE matches for this environment." />
        )}
      </Panel>
    </div>
  );
}
