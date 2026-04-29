import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getHuntingQueries } from '../../services/api';
import type { HuntingQuery, Paginated } from '../../services/api';
import { Radar } from 'lucide-react';

export function ThreatHunting() {
  const [data, setData] = useState<Paginated<HuntingQuery> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getHuntingQueries(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="Threat Hunting">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Queries" value={data?.total ?? 0} color="blue" />
          <MetricCard label="KQL" value={data?.items.filter((q) => q.data_source === 'kql').length ?? 0} color="purple" />
          <MetricCard label="SQL" value={data?.items.filter((q) => q.data_source === 'sql').length ?? 0} color="orange" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Radar className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Hunting Query Library</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No queries" /> : (
            <div className="space-y-3 p-4">
              {data?.items.map((q) => (
                <div key={q.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <p className="text-sm font-medium text-gray-200">{q.name}</p>
                      <p className="text-xs text-gray-600 mt-0.5">{q.description}</p>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      <span className="badge badge-purple">{q.data_source}</span>
                      {q.mitre_techniques?.slice(0, 1).map((t) => <span key={t} className="badge badge-info">{t}</span>)}
                    </div>
                  </div>
                  <pre className="text-xs bg-gray-950 text-green-400 p-3 rounded-lg overflow-x-auto font-mono">{q.query}</pre>
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
