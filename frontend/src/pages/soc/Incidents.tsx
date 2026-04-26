import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getIncidents } from '../../services/api';
import type { Incident, Paginated } from '../../services/api';
import { FlameKindling } from 'lucide-react';

export function Incidents() {
  const [data, setData] = useState<Paginated<Incident> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getIncidents(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Incidents">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Critical" value={data?.items.filter((i) => i.severity === 'critical').length ?? 0} color="red" />
          <MetricCard label="Open" value={data?.items.filter((i) => i.status === 'open').length ?? 0} color="orange" />
          <MetricCard label="Resolved" value={data?.items.filter((i) => i.status === 'resolved').length ?? 0} color="green" />
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <FlameKindling className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-semibold text-gray-300">Active Incidents</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? (
            <EmptyState icon={<FlameKindling className="w-10 h-10" />} title="No incidents" />
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Severity</th><th>Title</th><th>Type</th><th>Status</th><th>Assigned To</th><th>Created</th></tr></thead>
                <tbody>
                  {data?.items.map((i) => (
                    <tr key={i.id}>
                      <td><SeverityBadge severity={i.severity} /></td>
                      <td>
                        <div className="font-medium text-gray-200 text-sm">{i.title}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{i.description}</div>
                      </td>
                      <td className="text-gray-500 text-xs">{i.incident_type?.replace(/_/g, ' ')}</td>
                      <td><StatusBadge status={i.status} /></td>
                      <td className="text-gray-500 text-xs">{i.assigned_to}</td>
                      <td className="text-gray-600 text-xs">{new Date(i.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="px-4 pb-4"><Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} /></div>
        </div>
      </div>
    </Layout>
  );
}
