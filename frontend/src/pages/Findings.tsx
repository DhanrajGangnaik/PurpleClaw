import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Asset, Finding, FindingSeverity } from '../types/api';
import { formatDate } from '../utils';

interface FindingsProps {
  assets: Asset[];
  findings: Finding[];
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
  if (severity === 'low') {
    return 'cyan';
  }
  return 'slate';
}

export function Findings({ assets, findings, loading, error }: FindingsProps) {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const assetId = params.get('asset');
  const assetNames = useMemo(() => Object.fromEntries(assets.map((asset) => [asset.id, asset.name])), [assets]);
  const filteredFindings = assetId ? findings.filter((finding) => finding.asset_id === assetId) : findings;
  const filterAsset = assetId ? assetNames[assetId] ?? assetId : null;
  const columns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Finding', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'asset', label: 'Asset', render: (finding) => assetNames[finding.asset_id] ?? finding.asset_id },
    { key: 'severity', label: 'Severity', render: (finding) => <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} /> },
    { key: 'category', label: 'Category', render: (finding) => <StatusBadge label={finding.category} tone="cyan" /> },
    { key: 'status', label: 'Status', render: (finding) => <StatusBadge label={finding.status} tone={finding.status === 'open' ? 'purple' : 'green'} /> },
    { key: 'updated', label: 'Updated', render: (finding) => formatDate(finding.updated_at) },
  ];

  return (
    <Panel
      title={filterAsset ? `Findings for ${filterAsset}` : 'Findings Register'}
      eyebrow={assetId ? 'Asset Findings' : 'Posture Findings'}
    >
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading findings from PurpleClaw...</div>
      ) : (
        <DataTable
          columns={columns}
          rows={filteredFindings}
          getRowKey={(finding) => finding.id}
          emptyText="No findings matched this view."
          onRowClick={(finding) => navigate(`/remediation?finding=${finding.id}`)}
        />
      )}
    </Panel>
  );
}
