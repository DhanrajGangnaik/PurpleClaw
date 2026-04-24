import { WidgetEmptyState } from '../WidgetEmptyState';
import { getReportDownloadUrl } from '../../../services/api';
import type { ReportListWidgetPayload } from '../../../types/api';

interface ReportListWidgetProps {
  widget: ReportListWidgetPayload;
}

export function ReportListWidget({ widget }: ReportListWidgetProps) {
  if (!Array.isArray(widget.data) || widget.data.length === 0) {
    return <WidgetEmptyState message="No reports are available." />;
  }

  return (
    <div className="space-y-3">
      {widget.data.map((report) => (
        <div key={report.report_id} className="theme-inset rounded-2xl p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="theme-text-primary font-medium">{report.title}</span>
            {report.status === 'ready' ? (
              <a href={getReportDownloadUrl(report.report_id)} className="theme-brand text-sm font-semibold underline underline-offset-4">
                PDF
              </a>
            ) : (
              <span className="theme-text-faint text-sm">Unavailable</span>
            )}
          </div>
          <p className="theme-text-muted mt-2 text-sm">{report.generated_from}</p>
        </div>
      ))}
    </div>
  );
}
