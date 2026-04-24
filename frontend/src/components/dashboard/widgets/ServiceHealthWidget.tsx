import { StatusBadge } from '../../StatusBadge';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { ServiceHealthWidgetPayload } from '../../../types/api';

interface ServiceHealthWidgetProps {
  widget: ServiceHealthWidgetPayload;
}

export function ServiceHealthWidget({ widget }: ServiceHealthWidgetProps) {
  if (!Array.isArray(widget.data) || widget.data.length === 0) {
    return <WidgetEmptyState message="No service health data is available." />;
  }

  return (
    <div className="space-y-3">
      {widget.data.map((service) => (
        <div key={service.service_id} className="theme-inset rounded-2xl p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="theme-text-primary font-medium">{service.name}</span>
            <StatusBadge label={service.status} tone={service.status === 'healthy' ? 'green' : service.status === 'degraded' ? 'amber' : 'red'} />
          </div>
          <p className="theme-text-muted mt-2 text-sm">
            Availability {service.availability}% · Latency {service.latency_ms ?? 'n/a'} ms
          </p>
        </div>
      ))}
    </div>
  );
}
