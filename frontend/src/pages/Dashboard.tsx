import { useEffect, useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { MetricCard, PageLoading, SeverityBadge, StatusBadge } from '../components/ui';
import { getDashboardStats, getDashboardAlertsTrend, getDashboardTopThreats } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { AlertTriangle, Shield, Bug, Activity, Target, CheckSquare } from 'lucide-react';

export function Dashboard() {
  const [stats, setStats] = useState<Record<string, number>>({});
  const [trend, setTrend] = useState<unknown[]>([]);
  const [threats, setThreats] = useState<unknown[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([getDashboardStats(), getDashboardAlertsTrend(), getDashboardTopThreats()])
      .then(([s, t, th]) => {
        if (s.status === 'fulfilled') setStats(s.value as Record<string, number>);
        if (t.status === 'fulfilled') setTrend(t.value as unknown[]);
        if (th.status === 'fulfilled') setThreats(th.value as unknown[]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout title="Dashboard"><PageLoading /></Layout>;

  return (
    <Layout title="Dashboard">
      <div className="space-y-6">
        {/* Top metrics */}
        <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          <MetricCard label="Open Alerts" value={stats.open_alerts ?? 0} color="red" />
          <MetricCard label="Active Incidents" value={stats.active_incidents ?? 0} color="orange" />
          <MetricCard label="Total Assets" value={stats.total_assets ?? 0} color="blue" />
          <MetricCard label="Critical Findings" value={stats.critical_findings ?? 0} color="red" />
          <MetricCard label="Active IOCs" value={stats.active_iocs ?? stats.ioc_count ?? 0} color="purple" />
          <MetricCard label="Coverage %" value={`${stats.mitre_coverage ?? 0}%`} color="green" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Alert trend */}
          <div className="lg:col-span-2 card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Activity className="w-4 h-4 text-purple-400" /> Alert Trend (7 days)
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={trend as Record<string, unknown>[]}>
                <defs>
                  <linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                <Area type="monotone" dataKey="count" stroke="#7c3aed" fill="url(#alertGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Top threats */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Target className="w-4 h-4 text-red-400" /> Top Threat Actors
            </h3>
            <div className="space-y-3">
              {(threats as Array<Record<string, unknown>>).slice(0, 6).map((t, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-purple-900 flex items-center justify-center text-xs text-purple-300 font-bold">{i + 1}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-300 truncate">{String(t.name)}</p>
                    <p className="text-xs text-gray-600">{String(t.origin_country)}</p>
                  </div>
                  <span className="badge badge-purple text-xs">{String(t.sophistication)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Security posture */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4 text-purple-400" /> Security Posture
            </h3>
            <div className="space-y-3">
              {[
                { label: 'SIEM Coverage', value: stats.siem_coverage ?? 85 },
                { label: 'Patch Compliance', value: stats.patch_compliance ?? 72 },
                { label: 'ATT&CK Coverage', value: stats.mitre_coverage ?? 68 },
                { label: 'Playbook Readiness', value: stats.playbook_readiness ?? 90 },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>{item.label}</span><span>{item.value}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-purple-600 rounded-full transition-all" style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Finding distribution */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
              <Bug className="w-4 h-4 text-orange-400" /> Finding Distribution
            </h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={[
                { name: 'Critical', count: stats.critical_findings ?? 5, fill: '#ef4444' },
                { name: 'High', count: stats.high_findings ?? 12, fill: '#f97316' },
                { name: 'Medium', count: stats.medium_findings ?? 18, fill: '#eab308' },
                { name: 'Low', count: stats.low_findings ?? 25, fill: '#3b82f6' },
              ]}>
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8 }} />
                <Bar dataKey="count" fill="#7c3aed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </Layout>
  );
}
