import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getPayloads } from '../../services/api';
import type { Payload, Paginated } from '../../services/api';
import { Cpu } from 'lucide-react';

export function Payloads() {
  const [data, setData] = useState<Paginated<Payload> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getPayloads(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Payloads">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total" value={data?.total ?? 0} color="red" />
          {/* obfuscated/detected_by_av not stored in backend model */}
          <MetricCard label="Shellcode" value={data?.items.filter((p) => p.type === 'shellcode').length ?? 0} color="orange" />
          <MetricCard label="Scripts" value={data?.items.filter((p) => p.type === 'script').length ?? 0} color="purple" />
          <MetricCard label="Executables" value={data?.items.filter((p) => p.type === 'executable').length ?? 0} color="green" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">Payload Library</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<Cpu className="w-10 h-10" />} title="No payloads" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name</th><th>Type</th><th>Platform</th><th>Tags</th><th>Created</th></tr></thead>
                <tbody>
                  {data?.items.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <div className="font-medium text-gray-200">{p.name}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{p.description}</div>
                      </td>
                      <td><span className="badge badge-purple">{p.type}</span></td>
                      <td className="text-gray-500 text-xs">{p.platform}</td>
                      <td className="text-gray-500 text-xs">{p.tags?.slice(0, 3).join(', ')}</td>
                      <td className="text-gray-600 text-xs">{new Date(p.created_at).toLocaleDateString()}</td>
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
