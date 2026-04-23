import { DataTable, type DataColumn } from '../../DataTable';
import { StatusBadge } from '../../StatusBadge';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { Finding, FindingsTableWidgetPayload } from '../../../types/api';

interface FindingsTableWidgetProps {
  widget: FindingsTableWidgetPayload;
}

export function FindingsTableWidget({ widget }: FindingsTableWidgetProps) {
  if (!Array.isArray(widget.data) || widget.data.length === 0) {
    return <WidgetEmptyState message="No findings available for this widget." />;
  }
  const columns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Finding', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'severity', label: 'Severity', render: (finding) => <StatusBadge label={finding.severity} tone={finding.severity === 'critical' || finding.severity === 'high' ? 'red' : finding.severity === 'medium' ? 'purple' : 'cyan'} /> },
    { key: 'score', label: 'Risk Score', render: (finding) => finding.score },
  ];
  return <DataTable columns={columns} rows={widget.data} getRowKey={(finding) => finding.id} emptyText="No findings available." />;
}
