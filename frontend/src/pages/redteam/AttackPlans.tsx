import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getAttackPlans, executeAttackPlan } from '../../services/api';
import type { AttackPlan, Paginated } from '../../services/api';
import { Target, Play } from 'lucide-react';
import toast from 'react-hot-toast';

export function AttackPlans() {
  const [data, setData] = useState<Paginated<AttackPlan> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); getAttackPlans(page, 25).then(setData).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, [page]);

  const execute = async (id: number) => {
    try { await executeAttackPlan(id); toast.success('Attack plan executing…'); load(); }
    catch { toast.error('Execution failed'); }
  };

  return (
    <Layout title="Attack Plans">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Plans" value={data?.total ?? 0} color="red" />
          <MetricCard label="Active" value={data?.items.filter((p) => p.status === 'active').length ?? 0} color="orange" />
          <MetricCard label="Completed" value={data?.items.filter((p) => p.status === 'completed').length ?? 0} color="green" />
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Target className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">Attack Plans</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<Target className="w-10 h-10" />} title="No attack plans" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name</th><th>Objective</th><th>Tactics</th><th>Status</th><th>Actions</th></tr></thead>
                <tbody>
                  {data?.items.map((p) => (
                    <tr key={p.id}>
                      <td className="font-medium text-gray-200">{p.name}</td>
                      <td className="text-gray-500 text-xs max-w-xs truncate">{p.objective}</td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {p.mitre_tactics?.slice(0, 3).map((t) => <span key={t} className="badge badge-purple text-xs">{t}</span>)}
                        </div>
                      </td>
                      <td><StatusBadge status={p.status} /></td>
                      <td>
                        {p.status !== 'completed' && (
                          <button onClick={() => execute(p.id)} className="flex items-center gap-1 text-xs text-green-400 hover:text-green-300 transition-colors">
                            <Play className="w-3 h-3" /> Execute
                          </button>
                        )}
                      </td>
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
