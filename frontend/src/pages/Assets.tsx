import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Asset, Finding } from '../types/api';
import { formatDate } from '../utils';

interface AssetsProps {
  assets: Asset[];
  findings: Finding[];
  loading: boolean;
  error: string | null;
}

function riskTone(score: number) {
  if (score >= 85) {
    return 'red';
  }
  if (score >= 60) {
    return 'purple';
  }
  return 'green';
}

export function Assets({ assets, findings, loading, error }: AssetsProps) {
  const navigate = useNavigate();
  const findingCounts = useMemo(
    () =>
      findings.reduce<Record<string, number>>((counts, finding) => {
        counts[finding.asset_id] = (counts[finding.asset_id] ?? 0) + 1;
        return counts;
      }, {}),
    [findings],
  );
  const columns: DataColumn<Asset>[] = [
    { key: 'name', label: 'Asset', render: (asset) => <span className="theme-text-primary font-medium">{asset.name}</span> },
    { key: 'type', label: 'Type', render: (asset) => <StatusBadge label={asset.asset_type} tone="cyan" /> },
    { key: 'exposure', label: 'Exposure', render: (asset) => asset.exposure },
    { key: 'risk', label: 'Risk', render: (asset) => <StatusBadge label={String(asset.risk_score)} tone={riskTone(asset.risk_score)} /> },
    { key: 'findings', label: 'Findings', render: (asset) => findingCounts[asset.id] ?? 0 },
    { key: 'owner', label: 'Owner', render: (asset) => asset.owner },
    { key: 'last_seen', label: 'Last Seen', render: (asset) => formatDate(asset.last_seen) },
  ];

  return (
    <Panel title="Asset Inventory" eyebrow="Exposure Management">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading assets from PurpleClaw...</div>
      ) : (
        <DataTable
          columns={columns}
          rows={assets}
          getRowKey={(asset) => asset.id}
          emptyText="No assets returned by the API."
          onRowClick={(asset) => navigate(`/findings?asset=${asset.id}`)}
        />
      )}
    </Panel>
  );
}
