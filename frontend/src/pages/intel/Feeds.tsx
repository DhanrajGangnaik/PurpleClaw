import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, EmptyState } from '../../components/ui';
import { getThreatFeeds } from '../../services/api';
import type { ThreatFeed } from '../../services/api';
import { Radar, RefreshCw } from 'lucide-react';

export function Feeds() {
  const [feeds, setFeeds] = useState<ThreatFeed[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); getThreatFeeds().then(setFeeds).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, []);

  return (
    <Layout title="Threat Feeds">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Feeds" value={feeds.length} color="purple" />
          <MetricCard label="Active" value={feeds.filter((f) => f.enabled).length} color="green" />
          <MetricCard label="Total IOCs" value={feeds.reduce((s, f) => s + f.ioc_count, 0).toLocaleString()} color="red" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Radar className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Threat Intelligence Feeds</h2>
            <button onClick={load} className="ml-auto btn-secondary p-2"><RefreshCw className="w-4 h-4" /></button>
          </div>
          {loading ? <PageLoading /> : feeds.length === 0 ? <EmptyState title="No feeds" /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
              {feeds.map((f) => (
                <div key={f.id} className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
                  <div className="flex items-start gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${f.enabled ? 'bg-green-500' : 'bg-gray-600'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-200 text-sm">{f.name}</span>
                        <span className="badge badge-info text-xs">{f.type}</span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{f.description}</p>
                      <div className="flex justify-between text-xs text-gray-600">
                        <span>IOCs: <span className="text-gray-400 font-medium">{f.ioc_count.toLocaleString()}</span></span>
                        <span>Updated: {f.last_fetched ? new Date(f.last_fetched).toLocaleDateString() : '—'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
