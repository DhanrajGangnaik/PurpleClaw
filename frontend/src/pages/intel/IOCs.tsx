import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getIOCs } from '../../services/api';
import type { IOC, Paginated } from '../../services/api';
import { Crosshair } from 'lucide-react';

export function IOCs() {
  const [data, setData] = useState<Paginated<IOC> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    getIOCs(page, 50, typeFilter || undefined).then(setData).finally(() => setLoading(false));
  }, [page, typeFilter]);

  return (
    <Layout title="Indicators of Compromise">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total IOCs" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Active" value={data?.items.filter((i) => i.active).length ?? 0} color="red" />
          <MetricCard label="IP Addresses" value={data?.items.filter((i) => i.type === 'ip').length ?? 0} color="blue" />
          <MetricCard label="Domains" value={data?.items.filter((i) => i.type === 'domain').length ?? 0} color="orange" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-3">
            <Crosshair className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">IOC Database</h2>
            <div className="ml-auto">
              <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="w-36">
                <option value="">All Types</option>
                {['ip','domain','hash','url','email','registry_key'].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No IOCs found" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Type</th><th>Value</th><th>Severity</th><th>Confidence</th><th>Source</th><th>Active</th><th>Last Seen</th></tr></thead>
                <tbody>
                  {data?.items.map((ioc) => (
                    <tr key={ioc.id}>
                      <td><span className="badge badge-purple">{ioc.type}</span></td>
                      <td className="font-mono text-xs text-gray-300 max-w-xs truncate">{ioc.value}</td>
                      <td><SeverityBadge severity={ioc.severity} /></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1 bg-gray-800 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-500 rounded-full" style={{ width: `${ioc.confidence}%` }} />
                          </div>
                          <span className="text-xs text-gray-600">{ioc.confidence}%</span>
                        </div>
                      </td>
                      <td className="text-gray-500 text-xs">{ioc.source}</td>
                      <td>{ioc.active ? <span className="text-red-400 text-xs">Active</span> : <span className="text-gray-600 text-xs">Inactive</span>}</td>
                      <td className="text-gray-600 text-xs">{new Date(ioc.last_seen).toLocaleDateString()}</td>
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
