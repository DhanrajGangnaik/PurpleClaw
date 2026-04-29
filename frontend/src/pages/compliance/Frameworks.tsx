import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, EmptyState } from '../../components/ui';
import { getComplianceFrameworks, getComplianceSummary } from '../../services/api';
import type { ComplianceFramework } from '../../services/api';
import { CheckSquare } from 'lucide-react';

export function Frameworks() {
  const [frameworks, setFrameworks] = useState<ComplianceFramework[]>([]);
  const [summary, setSummary] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getComplianceFrameworks(), getComplianceSummary()])
      .then(([f, s]) => { setFrameworks(f); setSummary(s); })
      .finally(() => setLoading(false));
  }, []);

  // Backend returns overall as 0-100 integer; by_framework is [{name, score}]
  const overall = typeof summary.overall === 'number' ? (summary.overall as number) / 100 : 0;
  const byFramework = Array.isArray(summary.by_framework) ? (summary.by_framework as { name: string; score: number }[]) : [];

  return (
    <Layout title="Compliance Frameworks">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Frameworks" value={frameworks.length} color="purple" />
          <MetricCard label="Overall Compliance" value={`${Math.round(overall * 100)}%`} color="green" />
          <MetricCard label="Total Controls" value={frameworks.reduce((s, f) => s + f.controls_count, 0)} color="blue" />
          <MetricCard label="Avg Score" value={`${Math.round(overall * 100)}%`} color="orange" />
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <CheckSquare className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Compliance Frameworks</h2>
          </div>
          {loading ? <PageLoading /> : frameworks.length === 0 ? <EmptyState title="No frameworks" /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {frameworks.map((f) => {
                // Look up score from by_framework array; fallback to 0
                const entry = byFramework.find((b) => b.name === f.name);
                const fComp = entry ? entry.score : 0;
                return (
                  <div key={f.id} className="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="text-sm font-bold text-gray-200">{f.name}</h3>
                        <p className="text-xs text-gray-600">v{f.version}</p>
                      </div>
                      <span className="text-lg font-bold text-purple-400">{Math.round(fComp)}%</span>
                    </div>
                    <div className="h-2 bg-gray-800 rounded-full overflow-hidden mb-3">
                      <div className={`h-full rounded-full ${fComp >= 80 ? 'bg-green-500' : fComp >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`} style={{ width: `${fComp}%` }} />
                    </div>
                    <p className="text-xs text-gray-600 mb-2">{f.description}</p>
                    <p className="text-xs text-gray-500">{f.controls_count} controls</p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
