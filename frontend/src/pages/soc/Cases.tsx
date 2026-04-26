import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getCases } from '../../services/api';
import type { Case, Paginated } from '../../services/api';
import { FolderOpen } from 'lucide-react';

export function Cases() {
  const [data, setData] = useState<Paginated<Case> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCases(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  const priorityColor = (p: string) =>
    p === 'critical' ? 'badge-critical' : p === 'high' ? 'badge-high' : p === 'medium' ? 'badge-medium' : 'badge-low';
  const tlpColor = (t: string) =>
    t === 'TLP:RED' ? 'text-red-400' : t === 'TLP:AMBER' ? 'text-yellow-400' : t === 'TLP:GREEN' ? 'text-green-400' : 'text-gray-400';

  return (
    <Layout title="Cases">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Cases" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Open" value={data?.items.filter((c) => c.status === 'open').length ?? 0} color="orange" />
          <MetricCard label="In Progress" value={data?.items.filter((c) => c.status === 'in_progress').length ?? 0} color="blue" />
          <MetricCard label="Closed" value={data?.items.filter((c) => c.status === 'closed').length ?? 0} color="green" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Forensic Cases</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<FolderOpen className="w-10 h-10" />} title="No cases" /> : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Title</th><th>Priority</th><th>Status</th><th>TLP</th>
                    <th>Incident</th><th>Tags</th><th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.items.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <div className="font-medium text-gray-200 text-sm">{c.title}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{c.description}</div>
                      </td>
                      <td><span className={`badge ${priorityColor(c.priority)}`}>{c.priority}</span></td>
                      <td><StatusBadge status={c.status} /></td>
                      <td><span className={`text-xs font-semibold ${tlpColor(c.tlp)}`}>{c.tlp}</span></td>
                      <td className="text-gray-500 text-xs">{c.incident_id ? `INC-${c.incident_id}` : '—'}</td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {c.tags?.slice(0, 3).map((t) => <span key={t} className="badge badge-info text-xs">{t}</span>)}
                        </div>
                      </td>
                      <td className="text-gray-600 text-xs">{new Date(c.created_at).toLocaleDateString()}</td>
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
