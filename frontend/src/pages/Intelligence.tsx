import { useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { MetricCard } from '../components/MetricCard';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { updateIntelligence } from '../services/api';
import type { Finding, FindingSeverity, IntelTrend, IntelligenceSummary, IntelligenceUpdateRun, ThreatAdvisory } from '../types/api';
import { formatDate } from '../utils';

interface IntelligenceProps {
  selectedEnvironmentId: string;
  summary: IntelligenceSummary | null;
  advisories: ThreatAdvisory[];
  trends: IntelTrend[];
  relevantFindings: Finding[];
  updateRuns: IntelligenceUpdateRun[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

function severityTone(severity: FindingSeverity) {
  if (severity === 'critical' || severity === 'high') {
    return 'red';
  }
  if (severity === 'medium') {
    return 'purple';
  }
  return 'cyan';
}

export function Intelligence({ selectedEnvironmentId, summary, advisories, trends, relevantFindings, updateRuns, loading, error, onDataChanged }: IntelligenceProps) {
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const advisoryColumns: DataColumn<ThreatAdvisory>[] = [
    { key: 'title', label: 'Relevant Advisories', render: (advisory) => <span className="theme-text-primary font-medium">{advisory.title}</span> },
    { key: 'source', label: 'Source', render: (advisory) => advisory.source_name },
    { key: 'severity', label: 'Severity', render: (advisory) => <StatusBadge label={advisory.severity} tone={severityTone(advisory.severity)} /> },
    { key: 'products', label: 'Products', render: (advisory) => advisory.affected_products.join(', ') },
    { key: 'published', label: 'Published', render: (advisory) => formatDate(advisory.published_at) },
  ];
  const trendColumns: DataColumn<IntelTrend>[] = [
    { key: 'title', label: 'Current Trends', render: (trend) => <span className="theme-text-primary font-medium">{trend.title}</span> },
    { key: 'category', label: 'Category', render: (trend) => <StatusBadge label={trend.category} tone="cyan" /> },
    { key: 'severity', label: 'Severity', render: (trend) => <StatusBadge label={trend.severity} tone={severityTone(trend.severity)} /> },
    { key: 'tech', label: 'Technologies', render: (trend) => trend.affected_technologies.join(', ') },
  ];
  const findingColumns: DataColumn<Finding>[] = [
    { key: 'title', label: 'Reprioritized Findings', render: (finding) => <span className="theme-text-primary font-medium">{finding.title}</span> },
    { key: 'score', label: 'Risk Score', render: (finding) => <StatusBadge label={String(finding.score)} tone={finding.score >= 85 ? 'red' : finding.score >= 60 ? 'purple' : 'cyan'} /> },
    { key: 'severity', label: 'Severity', render: (finding) => <StatusBadge label={finding.severity} tone={severityTone(finding.severity)} /> },
    { key: 'component', label: 'Component', render: (finding) => finding.affected_component ?? 'Context match' },
  ];
  const runColumns: DataColumn<IntelligenceUpdateRun>[] = [
    { key: 'run', label: 'Run', render: (run) => <span className="font-mono text-[var(--accent-cyan)]">{run.run_id}</span> },
    { key: 'status', label: 'Update Status', render: (run) => <StatusBadge label={run.status} tone={run.status === 'completed' ? 'green' : 'purple'} /> },
    { key: 'advisories', label: 'Advisories', render: (run) => run.advisories_loaded },
    { key: 'trends', label: 'Trends', render: (run) => run.trends_loaded },
    { key: 'findings', label: 'Findings', render: (run) => run.findings_reprioritized },
    { key: 'completed', label: 'Completed', render: (run) => formatDate(run.completed_at ?? undefined) },
  ];

  const handleUpdate = async () => {
    setRunning(true);
    setRunError(null);
    try {
      await updateIntelligence(selectedEnvironmentId);
      onDataChanged();
    } catch (errorValue) {
      setRunError(errorValue instanceof Error ? errorValue.message : 'Unable to update intelligence');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {(error || runError) && <div className="theme-error rounded-2xl p-4 text-sm">{error ?? runError}</div>}
      <Panel
        title="Intelligence Summary"
        eyebrow="Curated Context"
        action={
          <button type="button" onClick={handleUpdate} disabled={running} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60">
            {running ? 'Updating...' : 'Update Intelligence'}
          </button>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Update Status" value={loading ? '...' : summary?.source_health.status ?? 'unknown'} caption={summary?.source_health.notes ?? 'Source-controlled curated intelligence'} accent="green" />
          <MetricCard title="Relevant Advisories" value={loading ? '...' : summary?.relevant_advisories_count ?? 0} caption="Matched to inventory context" accent="cyan" />
          <MetricCard title="Current Trends" value={loading ? '...' : summary?.current_trends_count ?? 0} caption="Relevant technology trends" accent="purple" />
          <MetricCard title="Reprioritized Findings" value={loading ? '...' : summary?.reprioritized_findings_count ?? 0} caption="Deterministic score context" accent="pink" />
        </div>
      </Panel>

      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Relevant Advisories" eyebrow="Reviewable Sources">
          {loading ? <div className="theme-text-faint py-14 text-center text-sm">Loading advisories...</div> : <DataTable columns={advisoryColumns} rows={advisories} getRowKey={(advisory) => advisory.advisory_id} emptyText="No advisories available." />}
        </Panel>
        <Panel title="Current Trends" eyebrow="OSINT-style Context">
          {loading ? <div className="theme-text-faint py-14 text-center text-sm">Loading trends...</div> : <DataTable columns={trendColumns} rows={trends} getRowKey={(trend) => trend.trend_id} emptyText="No current trends available." />}
        </Panel>
      </div>

      <Panel title="Reprioritized Findings" eyebrow="Intelligence Enrichment">
        {loading ? <div className="theme-text-faint py-14 text-center text-sm">Loading reprioritized findings...</div> : <DataTable columns={findingColumns} rows={relevantFindings} getRowKey={(finding) => finding.id} emptyText="No findings matched curated intelligence context." />}
      </Panel>

      <Panel title="Update Status" eyebrow="Run History">
        {loading ? <div className="theme-text-faint py-14 text-center text-sm">Loading update history...</div> : <DataTable columns={runColumns} rows={updateRuns} getRowKey={(run) => run.run_id} emptyText="No intelligence updates have been run yet." />}
      </Panel>
    </div>
  );
}
