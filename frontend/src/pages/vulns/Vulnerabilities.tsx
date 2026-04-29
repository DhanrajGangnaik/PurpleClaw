import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getVulnerabilities } from '../../services/api';
import type { Vulnerability, Paginated } from '../../services/api';
import { Bug } from 'lucide-react';

export function Vulnerabilities() {
  const [data, setData] = useState<Paginated<Vulnerability> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getVulnerabilities(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Vulnerabilities">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total CVEs" value={data?.total ?? 0} color="orange" />
          <MetricCard label="Critical" value={data?.items.filter((v) => v.severity === 'critical').length ?? 0} color="red" />
          <MetricCard label="With Exploit" value={data?.items.filter((v) => v.exploit_available).length ?? 0} color="red" />
          <MetricCard label="Patchable" value={data?.items.filter((v) => v.patches?.length > 0).length ?? 0} color="green" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Bug className="w-4 h-4 text-orange-400" />
            <h2 className="text-sm font-semibold text-gray-300">Vulnerability Database</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No vulnerabilities" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>CVE ID</th><th>Title</th><th>CVSS</th><th>Severity</th><th>Exploit</th><th>Patch</th><th>Published</th></tr></thead>
                <tbody>
                  {data?.items.map((v) => (
                    <tr key={v.id}>
                      <td className="font-mono text-xs text-purple-400">{v.cve_id}</td>
                      <td>
                        <div className="font-medium text-gray-200 text-sm">{v.title}</div>
                        <div className="text-xs text-gray-600 truncate max-w-xs">{v.description?.slice(0, 80)}…</div>
                      </td>
                      <td>
                        <span className={`text-sm font-bold ${v.cvss_score >= 9 ? 'text-red-400' : v.cvss_score >= 7 ? 'text-orange-400' : 'text-yellow-400'}`}>
                          {v.cvss_score}
                        </span>
                      </td>
                      <td><SeverityBadge severity={v.severity} /></td>
                      <td>{v.exploit_available ? <span className="text-red-400 text-xs font-medium">Yes</span> : <span className="text-gray-600 text-xs">No</span>}</td>
                      <td>{v.patches?.length > 0 ? <span className="text-green-400 text-xs font-medium">Yes</span> : <span className="text-gray-600 text-xs">No</span>}</td>
                      <td className="text-gray-600 text-xs">{v.published_at ? new Date(v.published_at).toLocaleDateString() : '-'}</td>
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
