import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getFindings } from '../../services/api';
import type { Finding, Paginated } from '../../services/api';
import { AlertTriangle } from 'lucide-react';

export function Findings() {
  const [data, setData] = useState<Paginated<Finding> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    setLoading(true);
    getFindings(page, 25, statusFilter || undefined).then(setData).finally(() => setLoading(false));
  }, [page, statusFilter]);

  return (
    <Layout title="Findings">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total" value={data?.total ?? 0} color="orange" />
          <MetricCard label="Critical" value={data?.items.filter((f) => f.severity === 'critical').length ?? 0} color="red" />
          <MetricCard label="Open" value={data?.items.filter((f) => f.status === 'open').length ?? 0} color="orange" />
          <MetricCard label="Verified" value={data?.items.filter((f) => f.verified).length ?? 0} color="purple" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-semibold text-gray-300">Security Findings</h2>
            <div className="ml-auto">
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-36">
                <option value="">All Statuses</option>
                {['open','in_progress','resolved','accepted','false_positive'].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No findings" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Severity</th><th>Asset</th><th>Vuln ID</th><th>Status</th><th>Risk Score</th><th>Assigned To</th><th>First Seen</th></tr></thead>
                <tbody>
                  {data?.items.map((f) => (
                    <tr key={f.id}>
                      <td><SeverityBadge severity={f.severity} /></td>
                      <td className="text-gray-400 text-xs">Asset #{f.asset_id}</td>
                      <td className="text-gray-400 text-xs">Vuln #{f.vulnerability_id}</td>
                      <td><StatusBadge status={f.status} /></td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${f.risk_score > 70 ? 'bg-red-500' : f.risk_score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${f.risk_score}%` }} />
                          </div>
                          <span className="text-xs text-gray-500">{f.risk_score}</span>
                        </div>
                      </td>
                      <td className="text-gray-500 text-xs">{f.assigned_to}</td>
                      <td className="text-gray-600 text-xs">{new Date(f.first_seen).toLocaleDateString()}</td>
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
