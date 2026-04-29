import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getCampaigns } from '../../services/api';
import type { Campaign, Paginated } from '../../services/api';
import { Globe } from 'lucide-react';

export function Campaigns() {
  const [data, setData] = useState<Paginated<Campaign> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getCampaigns(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Campaigns">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Active" value={data?.items.filter((c) => c.status === 'active').length ?? 0} color="red" />
          <MetricCard label="Historical" value={data?.items.filter((c) => c.status === 'concluded').length ?? 0} color="blue" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Globe className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Threat Campaigns</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No campaigns" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name</th><th>Status</th><th>Targets</th><th>Techniques</th><th>Start Date</th></tr></thead>
                <tbody>
                  {data?.items.map((c) => (
                    <tr key={c.id}>
                      <td>
                        <div className="font-medium text-gray-200">{c.name}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{c.description}</div>
                      </td>
                      <td><StatusBadge status={c.status} /></td>
                      <td className="text-gray-500 text-xs">{c.targets?.slice(0, 2).join(', ')}</td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {c.ttps?.slice(0, 3).map((t) => <span key={t} className="badge badge-purple text-xs">{t}</span>)}
                        </div>
                      </td>
                      <td className="text-gray-600 text-xs">{new Date(c.start_date).toLocaleDateString()}</td>
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
