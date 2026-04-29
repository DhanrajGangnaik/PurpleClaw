import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getPlaybooks, executePlaybook } from '../../services/api';
import type { Playbook, Paginated } from '../../services/api';
import { BookOpen, Play } from 'lucide-react';
import toast from 'react-hot-toast';

export function Playbooks() {
  const [data, setData] = useState<Paginated<Playbook> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); getPlaybooks(page, 25).then(setData).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, [page]);

  const run = async (id: number) => {
    try { await executePlaybook(id); toast.success('Playbook executing'); load(); }
    catch { toast.error('Execution failed'); }
  };

  return (
    <Layout title="IR Playbooks">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Playbooks" value={data?.total ?? 0} color="blue" />
          <MetricCard label="Total Steps" value={data?.items.reduce((s, p) => s + (Array.isArray(p.steps_json) ? p.steps_json.length : 0), 0) ?? 0} color="green" />
          <MetricCard label="Types" value={[...new Set(data?.items.map((p) => p.type) ?? [])].length} color="purple" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">IR Playbooks</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No playbooks" /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
              {data?.items.map((p) => (
                <div key={p.id} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-200">{p.name}</h3>
                      <div className="flex gap-2 mt-1">
                        <span className="badge badge-purple">{p.type}</span>
                      </div>
                    </div>
                    <button onClick={() => run(p.id)} className="btn-primary flex items-center gap-1 py-1.5 px-3">
                      <Play className="w-3 h-3" /> Run
                    </button>
                  </div>
                  <p className="text-xs text-gray-600 mb-3">{p.description}</p>
                  <div>
                    <p className="text-xs text-gray-600 mb-1">Steps ({Array.isArray(p.steps_json) ? p.steps_json.length : 0})</p>
                    {Array.isArray(p.steps_json) && p.steps_json.slice(0, 3).map((step: unknown, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-gray-500 py-0.5">
                        <span className="w-4 h-4 rounded-full bg-purple-900/50 flex items-center justify-center text-purple-400 text-xs flex-shrink-0">{i+1}</span>
                        {typeof step === 'object' && step !== null && 'name' in step ? String((step as {name: string}).name) : String(step)}
                      </div>
                    ))}
                    {Array.isArray(p.steps_json) && p.steps_json.length > 3 && <p className="text-xs text-gray-700 ml-6">+{p.steps_json.length - 3} more steps</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="px-4 pb-4"><Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} /></div>
        </div>
      </div>
    </Layout>
  );
}
