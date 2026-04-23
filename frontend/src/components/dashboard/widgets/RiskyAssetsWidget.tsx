import { DataTable, type DataColumn } from '../../DataTable';
import { StatusBadge } from '../../StatusBadge';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { RiskByAsset, RiskyAssetsWidgetPayload } from '../../../types/api';

interface RiskyAssetsWidgetProps {
  widget: RiskyAssetsWidgetPayload;
}

export function RiskyAssetsWidget({ widget }: RiskyAssetsWidgetProps) {
  if (!Array.isArray(widget.data) || widget.data.length === 0) {
    return <WidgetEmptyState message="No risky assets were returned." />;
  }
  const columns: DataColumn<RiskByAsset>[] = [
    { key: 'asset', label: 'Asset', render: (asset) => <span className="theme-text-primary font-medium">{asset.asset_name}</span> },
    { key: 'score', label: 'Risk', render: (asset) => <StatusBadge label={String(asset.aggregate_score)} tone={asset.aggregate_score >= 80 ? 'red' : 'purple'} /> },
    { key: 'open', label: 'Open Findings', render: (asset) => asset.open_findings },
  ];
  return <DataTable columns={columns} rows={widget.data} getRowKey={(asset) => asset.asset_id} emptyText="No risky assets returned." />;
}
