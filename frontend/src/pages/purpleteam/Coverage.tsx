import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, EmptyState } from '../../components/ui';
import { getMitreTactics, getMitreTechniques, getAttackCoverage } from '../../services/api';
import type { MitreTactic, MitreTechnique, AttackCoverage } from '../../services/api';
import { CheckSquare } from 'lucide-react';

const coverageColor = (s: string) => s === 'covered' ? 'bg-green-800/60 border-green-700/50 text-green-300' : s === 'partial' ? 'bg-yellow-800/40 border-yellow-700/50 text-yellow-300' : 'bg-gray-800/60 border-gray-700/30 text-gray-600';

export function Coverage() {
  const [tactics, setTactics] = useState<MitreTactic[]>([]);
  const [techniques, setTechniques] = useState<MitreTechnique[]>([]);
  const [coverage, setCoverage] = useState<AttackCoverage[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string>('');

  useEffect(() => {
    Promise.all([getMitreTactics(), getMitreTechniques(), getAttackCoverage()])
      .then(([ta, te, co]) => { setTactics(ta); setTechniques(te); setCoverage(co); })
      .finally(() => setLoading(false));
  }, []);

  const covered = coverage.filter((c) => c.coverage_status === 'covered').length;
  const partial = coverage.filter((c) => c.coverage_status === 'partial').length;
  const total = coverage.length;
  const pct = total ? Math.round((covered + partial * 0.5) / total * 100) : 0;

  const covMap = new Map(coverage.map((c) => [c.technique_id, c]));
  const activeTactics = selected ? tactics.filter((t) => t.tactic_id === selected) : tactics;

  return (
    <Layout title="ATT&CK Coverage">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Coverage %" value={`${pct}%`} color="purple" />
          <MetricCard label="Covered" value={covered} color="green" />
          <MetricCard label="Partial" value={partial} color="yellow" />
          <MetricCard label="Not Covered" value={total - covered - partial} color="red" />
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <CheckSquare className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">MITRE ATT&CK Matrix</h2>
            <select value={selected} onChange={(e) => setSelected(e.target.value)} className="ml-auto w-48">
              <option value="">All Tactics</option>
              {tactics.map((t) => <option key={t.tactic_id} value={t.tactic_id}>{t.name}</option>)}
            </select>
          </div>

          {loading ? <PageLoading /> : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {activeTactics.map((tactic) => {
                const techsForTactic = techniques.filter((t) => t.tactic_id === tactic.id);
                return (
                  <div key={tactic.id} className="bg-gray-800/40 rounded-lg p-3 border border-gray-700/30">
                    <div className="text-xs font-bold text-purple-400 mb-1">{tactic.tactic_id}</div>
                    <div className="text-xs font-semibold text-gray-300 mb-2">{tactic.name}</div>
                    <div className="space-y-1">
                      {techsForTactic.slice(0, 8).map((tech) => {
                        const cov = covMap.get(tech.id);
                        return (
                          <div key={tech.id} className={`text-xs px-2 py-1 rounded border ${coverageColor(cov?.coverage_status ?? 'not_covered')}`}>
                            {tech.technique_id}: {tech.name.slice(0, 20)}
                          </div>
                        );
                      })}
                      {techsForTactic.length > 8 && <div className="text-xs text-gray-600 pl-2">+{techsForTactic.length - 8} more</div>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
            <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-green-800/60 border border-green-700/50" />Covered</div>
            <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-yellow-800/40 border border-yellow-700/50" />Partial</div>
            <div className="flex items-center gap-1.5"><div className="w-3 h-3 rounded bg-gray-800/60 border border-gray-700/30" />Not Covered</div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
