import { WidgetEmptyState } from '../WidgetEmptyState';
import type { TelemetrySummaryWidgetPayload } from '../../../types/api';

interface TelemetrySummaryWidgetProps {
  widget: TelemetrySummaryWidgetPayload;
}

export function TelemetrySummaryWidget({ widget }: TelemetrySummaryWidgetProps) {
  if (!widget.data?.summaries?.length) {
    return <WidgetEmptyState message="No telemetry summaries are available." />;
  }
  return (
    <div className="space-y-3">
      {widget.data.summaries.map((summary) => (
        <div key={summary.id} className="theme-inset rounded-2xl border p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="theme-text-primary font-medium">{summary.source_name}</span>
            <span className="theme-text-faint text-sm">{summary.health_status}</span>
          </div>
          <p className="theme-text-muted mt-2 text-sm">
            {summary.asset_count} assets · {summary.event_count} events
          </p>
        </div>
      ))}
    </div>
  );
}
