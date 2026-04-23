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
        <div key={service.service_id} className="theme-inset rounded-2xl border p-4">
          <div className="flex items-center justify-between gap-3">
            <span className="theme-text-primary font-medium">{service.name}</span>
            <span className="theme-text-faint text-sm">{service.status}</span>
          </div>
          <p className="theme-text-muted mt-2 text-sm">
            Availability {service.availability}% · Latency {service.latency_ms ?? 'n/a'} ms
          </p>
        </div>
      ))}
    </div>
  );
}
