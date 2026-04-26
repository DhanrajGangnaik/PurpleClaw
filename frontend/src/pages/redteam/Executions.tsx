import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getAttackExecutions } from '../../services/api';
import type { AttackExecution, Paginated } from '../../services/api';
import { Swords } from 'lucide-react';

export function RedTeamExecutions() {
  const [data, setData] = useState<Paginated<AttackExecution> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAttackExecutions(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Red Team Executions">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total" value={data?.total ?? 0} color="red" />
          <MetricCard label="Running" value={data?.items.filter((e) => e.status === 'running').length ?? 0} color="orange" />
          <MetricCard label="Completed" value={data?.items.filter((e) => e.status === 'completed').length ?? 0} color="green" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Swords className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">Execution History</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<Swords className="w-10 h-10" />} title="No executions" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Plan ID</th><th>Status</th><th>Started</th><th>Completed</th><th>Notes</th></tr></thead>
                <tbody>
                  {data?.items.map((e) => (
                    <tr key={e.id}>
                      <td className="text-gray-400 font-mono text-xs">PLAN-{e.plan_id}</td>
                      <td><StatusBadge status={e.status} /></td>
                      <td className="text-gray-600 text-xs">{e.started_at ? new Date(e.started_at).toLocaleString() : '-'}</td>
                      <td className="text-gray-600 text-xs">{e.completed_at ? new Date(e.completed_at).toLocaleString() : '-'}</td>
                      <td className="text-gray-500 text-xs max-w-xs truncate">{e.notes}</td>
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
