import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState, SeverityBadge } from '../../components/ui';
import { getAssets } from '../../services/api';
import type { Asset, Paginated } from '../../services/api';
import { Server } from 'lucide-react';

// Backend status values: active/inactive/unknown/compromised/quarantined
const statusColor = (s: string) => s === 'active' ? 'text-green-400' : s === 'inactive' ? 'text-red-400' : 'text-yellow-400';

export function Assets() {
  const [data, setData] = useState<Paginated<Asset> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const load = (p = page) => {
    setLoading(true);
    getAssets(p, 25, search || undefined).then(setData).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [page]);

  return (
    <Layout title="Assets">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Assets" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Active" value={data?.items.filter((a) => a.status === 'active').length ?? 0} color="green" />
          <MetricCard label="Critical Risk" value={data?.items.filter((a) => a.criticality === 'critical').length ?? 0} color="red" />
          <MetricCard label="Avg Risk Score" value={data?.items.length ? Math.round(data.items.reduce((s, a) => s + a.risk_score, 0) / data.items.length) : 0} color="orange" />
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-3">
            <Server className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Asset Inventory</h2>
            <div className="ml-auto flex gap-2">
              <input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && load(1)} placeholder="Search hostname, IP..." className="w-56" />
            </div>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<Server className="w-10 h-10" />} title="No assets found" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Hostname</th><th>IP</th><th>Type</th><th>OS</th><th>Status</th><th>Criticality</th><th>Risk Score</th><th>Owner</th></tr></thead>
                <tbody>
                  {data?.items.map((a) => (
                    <tr key={a.id}>
                      <td className="font-medium text-gray-200">{a.hostname}</td>
                      <td className="font-mono text-xs text-gray-400">{a.ip_address}</td>
                      <td className="text-gray-500 text-xs">{a.type}</td>
                      <td className="text-gray-500 text-xs">{a.os}</td>
                      <td><span className={`text-xs font-medium ${statusColor(a.status)}`}>{a.status}</span></td>
                      <td><SeverityBadge severity={a.criticality} /></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${a.risk_score > 70 ? 'bg-red-500' : a.risk_score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${a.risk_score}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{a.risk_score}</span>
                        </div>
                      </td>
                      <td className="text-gray-500 text-xs">{a.owner}</td>
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
