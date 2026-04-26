import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getEDREvents } from '../../services/api';
import type { EDREvent, Paginated } from '../../services/api';
import { Eye } from 'lucide-react';

export function EDR() {
  const [data, setData] = useState<Paginated<EDREvent> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getEDREvents(page, 50).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="EDR Events">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Events" value={data?.total ?? 0} color="blue" />
          <MetricCard label="Critical" value={data?.items.filter((e) => e.severity === 'critical').length ?? 0} color="red" />
          <MetricCard label="Process" value={data?.items.filter((e) => e.event_type === 'process').length ?? 0} color="orange" />
          <MetricCard label="Network" value={data?.items.filter((e) => e.event_type === 'network').length ?? 0} color="purple" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Eye className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">EDR Event Stream</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No EDR events" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Severity</th><th>Event Type</th><th>Process</th><th>Command</th><th>User</th><th>MITRE</th><th>Time</th></tr></thead>
                <tbody>
                  {data?.items.map((e) => (
                    <tr key={e.id}>
                      <td><SeverityBadge severity={e.severity} /></td>
                      <td><span className="badge badge-info">{e.event_type}</span></td>
                      <td className="font-medium text-gray-200 text-xs">{e.process_name}</td>
                      <td className="font-mono text-xs text-gray-500 max-w-xs truncate">{e.command_line}</td>
                      <td className="text-gray-500 text-xs">{e.user}</td>
                      <td className="text-gray-600 text-xs">{e.mitre_technique}</td>
                      <td className="text-gray-600 text-xs">{new Date(e.timestamp).toLocaleString()}</td>
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
