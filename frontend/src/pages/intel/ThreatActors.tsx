import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getThreatActors } from '../../services/api';
import type { ThreatActor, Paginated } from '../../services/api';
import { Users } from 'lucide-react';

const sophisticationColor = (s: string) => s === 'nation_state' ? 'badge-critical' : s === 'advanced' ? 'badge-high' : s === 'intermediate' ? 'badge-medium' : 'badge-low';

export function ThreatActors() {
  const [data, setData] = useState<Paginated<ThreatActor> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getThreatActors(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Threat Actors">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Known Actors" value={data?.total ?? 0} color="red" />
          <MetricCard label="Active" value={data?.items.filter((a) => a.active).length ?? 0} color="orange" />
          <MetricCard label="Nation State" value={data?.items.filter((a) => a.sophistication === 'nation_state').length ?? 0} color="purple" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Users className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">Threat Actor Intelligence</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No threat actors" /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
              {data?.items.map((a) => (
                <div key={a.id} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-10 h-10 rounded-full bg-red-900/50 flex items-center justify-center text-red-400 font-bold flex-shrink-0">
                      {a.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-200">{a.name}</span>
                        {a.active && <div className="w-2 h-2 rounded-full bg-red-500 pulse-ring" />}
                      </div>
                      <div className="flex gap-2 mt-1">
                        <span className={`badge ${sophisticationColor(a.sophistication)}`}>{a.sophistication}</span>
                        <span className="badge badge-info">{a.country}</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">{a.description}</p>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-gray-600">Motivation</p>
                      <p className="text-gray-400">{a.motivation}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Aliases</p>
                      <p className="text-gray-400">{a.aliases?.slice(0, 2).join(', ')}</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <p className="text-xs text-gray-600 mb-1">TTPs</p>
                    <div className="flex flex-wrap gap-1">
                      {a.ttps?.slice(0, 4).map((t) => <span key={t} className="badge badge-purple text-xs">{t}</span>)}
                    </div>
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
