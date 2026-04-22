import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { ServiceHealth as ServiceHealthRecord } from '../types/api';
import { formatDate } from '../utils';

interface ServiceHealthProps {
  services: ServiceHealthRecord[];
  loading: boolean;
  error: string | null;
}

function statusTone(status: string) {
  if (status === 'healthy') {
    return 'green';
  }
  if (status === 'degraded') {
    return 'purple';
  }
  return 'red';
}

export function ServiceHealth({ services, loading, error }: ServiceHealthProps) {
  return (
    <Panel title="Service Health" eyebrow="NOC Health Monitoring">
      {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
      {loading ? (
        <div className="theme-text-faint py-14 text-center text-sm">Loading service health from PurpleClaw...</div>
      ) : services.length === 0 ? (
        <div className="theme-text-faint py-14 text-center text-sm">No service health records returned by the API.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {services.map((service) => (
            <div key={service.service_id} className="theme-inset rounded-2xl border p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="theme-text-primary font-semibold">{service.name}</p>
                  <p className="theme-text-faint mt-1 text-xs">Updated {formatDate(service.updated_at)}</p>
                </div>
                <StatusBadge label={service.status} tone={statusTone(service.status)} />
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <div>
                  <p className="theme-text-faint text-xs uppercase tracking-[0.14em]">Availability</p>
                  <p className="theme-text-primary mt-2 text-2xl font-semibold">{service.availability}%</p>
                </div>
                <div>
                  <p className="theme-text-faint text-xs uppercase tracking-[0.14em]">Latency</p>
                  <p className="theme-text-primary mt-2 text-2xl font-semibold">{service.latency_ms ?? 'n/a'}</p>
                </div>
                <div>
                  <p className="theme-text-faint text-xs uppercase tracking-[0.14em]">Error Rate</p>
                  <p className="theme-text-primary mt-2 text-2xl font-semibold">{service.error_rate ?? 'n/a'}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
