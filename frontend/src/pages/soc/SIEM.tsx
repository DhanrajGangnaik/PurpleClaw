import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getLogSources, getLogEvents } from '../../services/api';
import type { LogSource, LogEvent, Paginated } from '../../services/api';
import { Activity, RefreshCw } from 'lucide-react';

const levelColor = (l: string) =>
  l === 'critical' || l === 'error' ? 'text-red-400'
  : l === 'warning' ? 'text-yellow-400'
  : l === 'info' ? 'text-blue-400' : 'text-gray-500';

const levelBg = (l: string) =>
  l === 'critical' || l === 'error' ? 'bg-red-900/20 border-red-800/30'
  : l === 'warning' ? 'bg-yellow-900/20 border-yellow-800/30'
  : 'bg-gray-900/40 border-gray-800/30';

export function SIEM() {
  const [sources, setSources] = useState<LogSource[]>([]);
  const [events, setEvents] = useState<Paginated<LogEvent> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState<number | undefined>(undefined);
  const [levelFilter, setLevelFilter] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([
      getLogSources(),
      getLogEvents(page, 50, selectedSource),
    ])
      .then(([s, e]) => { setSources(s); setEvents(e); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [page, selectedSource]);

  const totalEps = sources.reduce((s, src) => s + Math.round(src.events_per_day / 86400), 0);
  const filtered = levelFilter
    ? { ...events, items: events?.items.filter((e) => e.level === levelFilter) ?? [] } as Paginated<LogEvent>
    : events;

  return (
    <Layout title="SIEM">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Log Sources" value={sources.length} color="purple" />
          <MetricCard label="Active" value={sources.filter((s) => s.enabled).length} color="green" />
          <MetricCard label="Total Events" value={events?.total ?? 0} color="blue" />
          <MetricCard label="Events/Sec" value={totalEps || 0} color="orange" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Sources panel */}
          <div className="card">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-300">Log Sources</span>
              <button onClick={load} className="text-gray-600 hover:text-gray-400 transition-colors">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="divide-y divide-gray-800">
              <div
                onClick={() => setSelectedSource(undefined)}
                className={`p-3 flex items-center gap-3 cursor-pointer hover:bg-purple-900/10 transition-colors ${!selectedSource ? 'bg-purple-900/20' : ''}`}
              >
                <div className="w-2 h-2 rounded-full bg-purple-500 flex-shrink-0" />
                <span className="text-sm text-gray-300">All Sources</span>
                <span className="ml-auto text-xs text-gray-600">{events?.total}</span>
              </div>
              {sources.map((s) => (
                <div
                  key={s.id}
                  onClick={() => setSelectedSource(s.id)}
                  className={`p-3 flex items-center gap-3 cursor-pointer hover:bg-purple-900/10 transition-colors ${selectedSource === s.id ? 'bg-purple-900/20' : ''}`}
                >
                  <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.enabled ? 'bg-green-500' : 'bg-gray-600'}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">{s.name}</p>
                    <p className="text-xs text-gray-600">{s.type} · {s.events_per_day.toLocaleString()} evt/day</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Events panel */}
          <div className="lg:col-span-2 card">
            <div className="p-4 border-b border-gray-800 flex items-center gap-3">
              <Activity className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-semibold text-gray-300">Event Stream</h2>
              <div className="ml-auto flex gap-2">
                <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)} className="w-28 py-1 text-xs">
                  <option value="">All Levels</option>
                  {['critical', 'error', 'warning', 'info', 'debug'].map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
                <button onClick={load} className="btn-secondary p-1.5"><RefreshCw className="w-3.5 h-3.5" /></button>
              </div>
            </div>

            {loading ? <PageLoading /> : filtered?.items.length === 0 ? (
              <EmptyState title="No events" description="Try changing the source or level filter" />
            ) : (
              <div className="divide-y divide-gray-800/40 max-h-[520px] overflow-y-auto">
                {filtered?.items.map((e) => (
                  <div key={e.id} className={`px-4 py-3 hover:bg-purple-900/5 transition-colors border-l-2 ${e.rule_matches?.length ? 'border-red-600' : 'border-transparent'}`}>
                    <div className="flex items-start gap-2">
                      <span className={`text-xs font-bold font-mono flex-shrink-0 mt-0.5 ${levelColor(e.level)}`}>{e.level.toUpperCase()}</span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-300 leading-relaxed">{e.message}</p>
                        <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-600">
                          {e.source_ip && <span>src: <span className="font-mono text-gray-500">{e.source_ip}</span></span>}
                          {e.dest_ip && <span>dst: <span className="font-mono text-gray-500">{e.dest_ip}</span></span>}
                          {e.username && <span>user: <span className="text-gray-500">{e.username}</span></span>}
                          {e.process_name && <span>proc: <span className="text-gray-500">{e.process_name}</span></span>}
                          <span className="ml-auto">{new Date(e.timestamp).toLocaleTimeString()}</span>
                        </div>
                        {e.rule_matches?.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {e.rule_matches.map((r) => <span key={r} className="badge badge-critical text-xs">{r}</span>)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="px-4 pb-4"><Pagination page={page} pages={events?.pages ?? 1} onChange={setPage} /></div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
