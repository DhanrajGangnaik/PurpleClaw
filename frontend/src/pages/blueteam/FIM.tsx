import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getFIMRecords } from '../../services/api';
import type { FIMRecord, Paginated } from '../../services/api';
import { FileText } from 'lucide-react';

export function FIM() {
  const [data, setData] = useState<Paginated<FIMRecord> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getFIMRecords(page, 50).then(setData).finally(() => setLoading(false));
  }, [page]);

  // FIMRecord.status holds the event type (backend enum: ok/modified/missing/new)
  const evtColor = (t: string) => t === 'new' ? 'text-green-400' : t === 'missing' ? 'text-red-400' : t === 'modified' ? 'text-yellow-400' : 'text-blue-400';

  return (
    <Layout title="File Integrity Monitoring">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Events" value={data?.total ?? 0} color="blue" />
          <MetricCard label="Modified" value={data?.items.filter((r) => r.status === 'modified').length ?? 0} color="yellow" />
          <MetricCard label="New" value={data?.items.filter((r) => r.status === 'new').length ?? 0} color="green" />
          <MetricCard label="Missing" value={data?.items.filter((r) => r.status === 'missing').length ?? 0} color="red" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">FIM Events</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No FIM events" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Status</th><th>File Path</th><th>Asset</th><th>Time</th></tr></thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr key={r.id}>
                      <td><span className={`text-xs font-semibold ${evtColor(r.status)}`}>{r.status}</span></td>
                      <td className="font-mono text-xs text-gray-400 max-w-xs truncate">{r.path}</td>
                      <td className="text-gray-500 text-xs">Asset #{r.asset_id}</td>
                      <td className="text-gray-600 text-xs">{new Date(r.checked_at).toLocaleString()}</td>
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
