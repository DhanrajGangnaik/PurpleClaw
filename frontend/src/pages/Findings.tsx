import { useMemo, useState } from 'react';
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
  const [severityFilter, setSeverityFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const assetId = params.get('asset');
  const assetNames = useMemo(() => Object.fromEntries(assets.map((asset) => [asset.id, asset.name])), [assets]);
  const categories = useMemo(() => Array.from(new Set(findings.map((finding) => finding.category))).sort(), [findings]);
  const statuses = useMemo(() => Array.from(new Set(findings.map((finding) => finding.status))).sort(), [findings]);
  const filteredFindings = (assetId ? findings.filter((finding) => finding.asset_id === assetId) : findings)
    .filter((finding) => severityFilter === 'all' || finding.severity === severityFilter)
    .filter((finding) => categoryFilter === 'all' || finding.category === categoryFilter)
    .filter((finding) => statusFilter === 'all' || finding.status === statusFilter)
    .sort((a, b) => b.score - a.score);
  const filterAsset = assetId ? assetNames[assetId] ?? assetId : null;
  const columns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Finding', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'asset', label: 'Asset', render: (finding) => assetNames[finding.asset_id] ?? finding.asset_id },
    { key: 'score', label: 'Risk Score', render: (finding) => <StatusBadge label={String(finding.score)} tone={finding.score >= 85 ? 'red' : finding.score >= 60 ? 'purple' : 'cyan'} /> },
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
      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <label className="theme-text-muted text-sm">
          Severity
          <select
            value={severityFilter}
            onChange={(event) => setSeverityFilter(event.target.value)}
            className="theme-inset theme-text-primary mt-2 w-full rounded-2xl border px-3 py-2 text-sm outline-none"
          >
            <option value="all">All severities</option>
            {(['critical', 'high', 'medium', 'low', 'info'] as FindingSeverity[]).map((severity) => (
              <option key={severity} value={severity}>{severity}</option>
            ))}
          </select>
        </label>
        <label className="theme-text-muted text-sm">
          Category
          <select
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
            className="theme-inset theme-text-primary mt-2 w-full rounded-2xl border px-3 py-2 text-sm outline-none"
          >
            <option value="all">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </label>
        <label className="theme-text-muted text-sm">
          Status
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="theme-inset theme-text-primary mt-2 w-full rounded-2xl border px-3 py-2 text-sm outline-none"
          >
            <option value="all">All statuses</option>
            {statuses.map((status) => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
        </label>
      </div>
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
