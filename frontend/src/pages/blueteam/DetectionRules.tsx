import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getDetectionRules } from '../../services/api';
import type { DetectionRule, Paginated } from '../../services/api';
import { ShieldCheck } from 'lucide-react';

export function DetectionRules() {
  const [data, setData] = useState<Paginated<DetectionRule> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getDetectionRules(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Detection Rules">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Rules" value={data?.total ?? 0} color="blue" />
          <MetricCard label="Enabled" value={data?.items.filter((r) => r.enabled).length ?? 0} color="green" />
          <MetricCard label="Sigma Rules" value={data?.items.filter((r) => r.rule_type === 'sigma').length ?? 0} color="purple" />
          <MetricCard label="Avg FP Rate" value={`${data?.items.length ? Math.round(data.items.reduce((s, r) => s + r.false_positive_rate, 0) / data.items.length * 100) : 0}%`} color="orange" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Detection Rules</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No detection rules" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name</th><th>Type</th><th>Severity</th><th>MITRE Tactic</th><th>Enabled</th><th>FP Rate</th></tr></thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <div className="font-medium text-gray-200 text-sm">{r.name}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{r.description}</div>
                      </td>
                      <td><span className="badge badge-info">{r.rule_type}</span></td>
                      <td><SeverityBadge severity={r.severity} /></td>
                      <td className="text-gray-500 text-xs">{r.mitre_tactic}</td>
                      <td>
                        <div className={`w-8 h-4 rounded-full flex items-center px-0.5 ${r.enabled ? 'bg-green-600' : 'bg-gray-700'}`}>
                          <div className={`w-3 h-3 rounded-full bg-white transition-transform ${r.enabled ? 'translate-x-4' : ''}`} />
                        </div>
                      </td>
                      <td className="text-gray-500 text-xs">{(r.false_positive_rate * 100).toFixed(0)}%</td>
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
