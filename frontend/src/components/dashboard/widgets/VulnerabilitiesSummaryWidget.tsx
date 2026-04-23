import { StatusBadge } from '../../StatusBadge';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { VulnerabilitiesSummaryWidgetPayload } from '../../../types/api';

interface VulnerabilitiesSummaryWidgetProps {
  widget: VulnerabilitiesSummaryWidgetPayload;
}

export function VulnerabilitiesSummaryWidget({ widget }: VulnerabilitiesSummaryWidgetProps) {
  if (!widget.data) {
    return <WidgetEmptyState message="No vulnerability summary is available." />;
  }
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <StatusBadge label={`${widget.data.total} matches`} tone="purple" />
        {Object.entries(widget.data.severity_distribution).map(([severity, count]) => (
          <StatusBadge key={severity} label={`${severity}:${count}`} tone={severity === 'critical' || severity === 'high' ? 'red' : severity === 'medium' ? 'purple' : 'cyan'} />
        ))}
      </div>
      {widget.data.matches.length === 0 ? (
        <WidgetEmptyState message="No vulnerability matches found." />
      ) : (
        <div className="space-y-3">
          {widget.data.matches.map((finding) => (
            <div key={finding.id} className="theme-inset rounded-2xl border p-4">
              <div className="theme-text-primary font-medium">{finding.title}</div>
              <p className="theme-text-muted mt-2 text-sm">{finding.affected_component ?? 'Component not specified'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
