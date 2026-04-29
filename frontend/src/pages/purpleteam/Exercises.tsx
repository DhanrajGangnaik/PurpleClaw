import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getExercises } from '../../services/api';
import type { Exercise, Paginated } from '../../services/api';
import { BookOpen } from 'lucide-react';

export function Exercises() {
  const [data, setData] = useState<Paginated<Exercise> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getExercises(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Purple Team Exercises">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Exercises" value={data?.total ?? 0} color="purple" />
          <MetricCard label="In Progress" value={data?.items.filter((e) => e.status === 'in_progress').length ?? 0} color="orange" />
          <MetricCard label="Completed" value={data?.items.filter((e) => e.status === 'completed').length ?? 0} color="green" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Purple Team Exercises</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No exercises" /> : (
            <div className="space-y-4 p-4">
              {data?.items.map((ex) => (
                <div key={ex.id} className="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50">
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-gray-200">{ex.name}</h3>
                        <StatusBadge status={ex.status} />
                        <span className="badge badge-purple">{ex.type}</span>
                      </div>
                      <p className="text-xs text-gray-600 mt-1">{ex.description}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <p className="text-gray-600 mb-1">Red Team</p>
                      <div className="flex flex-wrap gap-1">{ex.red_team?.map((m) => <span key={m} className="badge badge-high">{m}</span>)}</div>
                    </div>
                    <div>
                      <p className="text-gray-600 mb-1">Blue Team</p>
                      <div className="flex flex-wrap gap-1">{ex.blue_team?.map((m) => <span key={m} className="badge badge-success">{m}</span>)}</div>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-xs text-gray-600 mb-1">Objectives</p>
                    <ul className="text-xs text-gray-400 space-y-0.5">
                      {ex.objectives?.map((o, i) => <li key={i} className="flex items-start gap-1.5"><span className="text-purple-500 mt-0.5">•</span>{o}</li>)}
                    </ul>
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
