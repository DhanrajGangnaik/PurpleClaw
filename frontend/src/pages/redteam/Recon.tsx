import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getReconRecords } from '../../services/api';
import type { ReconRecord, Paginated } from '../../services/api';
import { Search } from 'lucide-react';

export function Recon() {
  const [data, setData] = useState<Paginated<ReconRecord> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getReconRecords(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Reconnaissance">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Records" value={data?.total ?? 0} color="red" />
          <MetricCard label="OSINT" value={data?.items.filter((r) => r.type === 'osint').length ?? 0} color="purple" />
          <MetricCard label="Network" value={data?.items.filter((r) => r.type === 'network').length ?? 0} color="blue" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Search className="w-4 h-4 text-yellow-400" />
            <h2 className="text-sm font-semibold text-gray-300">Recon Records</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No recon records" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Target</th><th>Type</th><th>Source</th><th>Created</th></tr></thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr key={r.id}>
                      <td className="font-medium text-gray-200 font-mono text-xs">{r.target}</td>
                      <td><span className="badge badge-purple">{r.type}</span></td>
                      <td className="text-gray-500 text-xs">{r.source}</td>
                      <td className="text-gray-600 text-xs">{new Date(r.created_at).toLocaleString()}</td>
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
