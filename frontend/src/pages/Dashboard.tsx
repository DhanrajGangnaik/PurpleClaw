import { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { MetricCard, PageLoading } from '../components/ui';
import { getDashboardStats, getDashboardAlertsTrend, getDashboardTopThreats, getDashboardAssetRisk } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { Activity, Target, Shield, Bug } from 'lucide-react';

type Stats = Record<string, unknown>;

export function Dashboard() {
  const [stats, setStats] = useState<Stats>({});
  const [trend, setTrend] = useState<{ date: string; count: number }[]>([]);
  const [threats, setThreats] = useState<Record<string, unknown>[]>([]);
  const [assetRisk, setAssetRisk] = useState<{ name: string; risk_score: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    Promise.allSettled([
      getDashboardStats(),
      getDashboardAlertsTrend(),
      getDashboardTopThreats(),
      getDashboardAssetRisk(),
    ]).then(([s, t, th, ar]) => {
      if (s.status === 'fulfilled') setStats(s.value as Stats);
      else setError(true);
      if (t.status === 'fulfilled') setTrend(t.value as { date: string; count: number }[]);
      if (th.status === 'fulfilled') setThreats(th.value as Record<string, unknown>[]);
      if (ar.status === 'fulfilled') setAssetRisk(ar.value as { name: string; risk_score: number }[]);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout title="Dashboard"><PageLoading /></Layout>;

  const num = (key: string) => typeof stats[key] === 'number' ? (stats[key] as number) : 0;

  const postureItems = [
    { label: 'ATT&CK Coverage',  value: num('mitre_coverage') },
    { label: 'Compliance Score', value: num('compliance_score') },
    { label: 'Active Incidents', value: Math.max(0, 100 - num('active_incidents') * 10) },
    { label: 'Open Alerts',      value: Math.max(0, 100 - num('open_alerts') * 2) },
  ];

  const findingData = [
    { name: 'Critical', count: num('critical_findings'), color: '#ef4444' },
    { name: 'High',     count: num('high_findings'),     color: '#f97316' },
    { name: 'Medium',   count: num('medium_findings'),   color: '#eab308' },
    { name: 'Low',      count: num('low_findings'),      color: '#3b82f6' },
  ];

  return (
    <Layout title="Dashboard">
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-800/50 rounded-lg text-xs text-red-400">
          Some dashboard data could not be loaded. Showing partial results.
        </div>
      )}
      <div className="space-y-6">
        {/* Top metrics — all real values from /dashboard/stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <MetricCard label="Open Alerts"      value={num('open_alerts')}      color="red" />
          <MetricCard label="Active Incidents" value={num('active_incidents')} color="orange" />
          <MetricCard label="Total Assets"     value={num('total_assets')}     color="blue" />
          <MetricCard label="Critical Findings" value={num('critical_findings')} color="red" />
          <MetricCard label="Active IOCs"      value={num('active_iocs')}      color="purple" />
          <MetricCard label="Coverage %"       value={`${num('mitre_coverage')}%`} color="green" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Alert trend — real 7-day data from /dashboard/alerts-trend */}
          <div className="lg:col-span-2 card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" /> Alert Trend (7 days)
            </h3>
            {trend.length === 0 ? (
              <div className="h-[200px] flex items-center justify-center text-sm text-gray-600">No trend data available</div>
            ) : (
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={trend}>
                  <defs>
                    <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                  <Area type="monotone" dataKey="count" stroke="#7c3aed" fill="url(#alertGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Top threat actors — real data from /dashboard/top-threats */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-red-400" /> Top Threat Actors
            </h3>
            {threats.length === 0 ? (
              <div className="text-sm text-gray-600 text-center py-8">No threat actor data</div>
            ) : (
              <div className="space-y-3">
                {threats.slice(0, 6).map((t, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-purple-900 flex items-center justify-center text-xs text-purple-300 font-bold">{i + 1}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-300 truncate">{String(t.name ?? '')}</p>
                      <p className="text-xs text-gray-600">{String(t.country ?? '—')}</p>
                    </div>
                    <span className="badge badge-purple text-xs">{String(t.sophistication ?? '')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Security posture — derived from real stats */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" /> Security Posture
            </h3>
            <div className="space-y-3">
              {postureItems.map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{item.label}</span>
                    <span>{Math.round(item.value)}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${item.value >= 75 ? 'bg-green-600' : item.value >= 50 ? 'bg-yellow-600' : 'bg-red-600'}`}
                      style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Finding distribution — real counts from stats */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Bug className="w-4 h-4 text-orange-400" /> Finding Distribution
            </h3>
            {findingData.every((d) => d.count === 0) ? (
              <div className="h-[180px] flex items-center justify-center text-sm text-gray-600">No findings data</div>
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={findingData}>
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {findingData.map((entry, index) => (
                      <Cell key={index} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Top risky assets — real data from /dashboard/asset-risk */}
        {assetRisk.length > 0 && (
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Top Risky Assets</h3>
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
              {assetRisk.slice(0, 10).map((a) => (
                <div key={a.name} className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50">
                  <p className="text-xs font-medium text-gray-300 truncate">{a.name}</p>
                  <div className="mt-2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${a.risk_score > 70 ? 'bg-red-500' : a.risk_score > 40 ? 'bg-yellow-500' : 'bg-green-500'}`}
                      style={{ width: `${Math.min(100, a.risk_score)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-600 mt-1">Risk: {Math.round(a.risk_score)}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
