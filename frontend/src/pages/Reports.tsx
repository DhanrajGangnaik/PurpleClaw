import { DataTable, type DataColumn } from '../components/DataTable';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { Report } from '../types/api';
import { formatDate } from '../utils';

interface ReportsProps {
  reports: Report[];
  loading: boolean;
  error: string | null;
}

export function Reports({ reports, loading, error }: ReportsProps) {
  const columns: DataColumn<Report>[] = [
    { key: 'title', label: 'Report', render: (report) => <span className="theme-text-primary font-medium">{report.title}</span> },
    { key: 'type', label: 'Type', render: (report) => <StatusBadge label={report.report_type} tone="purple" /> },
    { key: 'period', label: 'Period', render: (report) => report.period },
    { key: 'generated', label: 'Generated', render: (report) => formatDate(report.generated_at) },
    { key: 'summary', label: 'Summary', render: (report) => <span className="block max-w-xl truncate">{report.summary}</span> },
  ];

  return (
    <Panel title="Posture Reports" eyebrow="Executive Reporting">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading reports from PurpleClaw...</div>
      ) : (
        <DataTable columns={columns} rows={reports} getRowKey={(report) => report.id} emptyText="No reports returned by the API." />
      )}
    </Panel>
  );
}
