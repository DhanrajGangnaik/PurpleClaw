import { useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { JsonPanel } from '../components/JsonPanel';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import type { ExercisePlan } from '../types/api';
import { formatDate } from '../utils';

interface PlansProps {
  plans: ExercisePlan[];
  loading: boolean;
  error: string | null;
}

export function Plans({ plans, loading, error }: PlansProps) {
  const [selectedPlan, setSelectedPlan] = useState<ExercisePlan | null>(null);
  const columns: DataColumn<ExercisePlan>[] = [
    { key: 'id', label: 'ID', render: (plan) => <span className="font-mono text-[var(--accent-cyan)]">{plan.id}</span> },
    { key: 'name', label: 'Name', render: (plan) => <span className="theme-text-primary font-medium">{plan.name}</span> },
    { key: 'environment', label: 'Environment', render: (plan) => <StatusBadge label={plan.environment} tone="cyan" /> },
    { key: 'risk_level', label: 'Risk', render: (plan) => <StatusBadge label={plan.risk_level} tone={plan.risk_level === 'high' ? 'red' : plan.risk_level === 'medium' ? 'purple' : 'green'} /> },
    { key: 'created_at', label: 'Created', render: (plan) => formatDate(plan.created_at) },
    { key: 'updated_at', label: 'Updated', render: (plan) => formatDate(plan.updated_at) },
  ];

  return (
    <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
      <Panel title="Plans Registry" eyebrow="Validation Planning">
        {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading plans from PurpleClaw...</div>
        ) : (
          <DataTable
            columns={columns}
            rows={plans}
            getRowKey={(plan) => plan.id}
            emptyText="No plans returned by the API. Validate a plan to populate the registry."
            onRowClick={setSelectedPlan}
          />
        )}
      </Panel>

      <Panel title="Plan Inspector" eyebrow="Detail">
        {selectedPlan ? (
          <div className="space-y-4">
            <div className="rounded-2xl border border-fuchsia-400/20 bg-fuchsia-400/10 p-4">
              <p className="theme-text-primary text-sm font-semibold">{selectedPlan.name}</p>
              <p className="theme-text-muted mt-1 text-sm">{selectedPlan.description}</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Targets</p>
                <p className="theme-text-primary mt-2 text-2xl font-semibold">{selectedPlan.scope.allowed_targets.length}</p>
              </div>
              <div className="theme-inset rounded-2xl p-4">
                <p className="theme-text-faint text-xs uppercase tracking-[0.16em]">Steps</p>
                <p className="theme-text-primary mt-2 text-2xl font-semibold">{selectedPlan.execution_steps.length}</p>
              </div>
            </div>
            <JsonPanel value={selectedPlan} className="max-h-[520px]" />
          </div>
        ) : (
          <div className="theme-text-faint py-14 text-center text-sm">Select a row to inspect the plan payload.</div>
        )}
      </Panel>
    </div>
  );
}
