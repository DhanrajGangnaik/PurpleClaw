import { useEffect, useMemo, useState } from 'react';
import { Panel } from '../components/Panel';
import { SectionHeader } from '../components/SectionHeader';
import { StatusBadge } from '../components/StatusBadge';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { WidgetEmptyState } from '../components/dashboard/WidgetEmptyState';
import { WidgetLoadingState } from '../components/dashboard/WidgetLoadingState';
import { WidgetSelectorModal, type WidgetDefinition } from '../components/dashboard/WidgetSelectorModal';
import { useFetch } from '../hooks/useFetch';
import { renderDashboardWidget } from '../lib/dashboard/widgetRegistry';
import { createDashboard, getRenderedDashboard, updateDashboard } from '../services/api';
import type { DashboardConfig, RegisteredDataSource, RenderedWidget } from '../types/api';

interface DashboardsProps {
  selectedEnvironmentId: string;
  dashboards: DashboardConfig[];
  datasources: RegisteredDataSource[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

interface DraftWidget {
  widget_id: string;
  type: string;
  title: string;
  datasource: string;
  limit: number;
}

const widgetDefinitions: WidgetDefinition[] = [
  { type: 'metric_card', label: 'Metric Card', description: 'Single KPI for the current environment.', category: 'kpi' },
  { type: 'findings_table', label: 'Findings Table', description: 'High-priority findings needing review.', category: 'analysis' },
  { type: 'risky_assets', label: 'Risky Assets', description: 'Top risky assets ranked by score.', category: 'analysis' },
  { type: 'vulnerabilities_summary', label: 'Vulnerability Summary', description: 'Severity mix for matched vulnerabilities.', category: 'analysis' },
  { type: 'service_health', label: 'Service Health', description: 'Critical service health without extra clutter.', category: 'analysis' },
  { type: 'telemetry_summary', label: 'Telemetry Summary', description: 'Monitoring coverage and ingestion health.', category: 'secondary' },
  { type: 'alerts_summary', label: 'Alerts Summary', description: 'Alert trend snapshot for the environment.', category: 'secondary' },
  { type: 'signals_summary', label: 'Signals Summary', description: 'Detection activity in a compact format.', category: 'secondary' },
  { type: 'report_list', label: 'Report List', description: 'Recent reports related to the environment.', category: 'secondary' },
];

const defaultWidgets: DraftWidget[] = [
  { widget_id: 'risk-score', type: 'metric_card', title: 'Risk Score', datasource: 'inventory', limit: 1 },
  { widget_id: 'open-findings', type: 'metric_card', title: 'Open Findings', datasource: 'scanner_results', limit: 1 },
  { widget_id: 'key-findings', type: 'findings_table', title: 'Key Findings', datasource: 'scanner_results', limit: 5 },
  { widget_id: 'risky-assets', type: 'risky_assets', title: 'Risky Assets', datasource: 'inventory', limit: 5 },
  { widget_id: 'service-health', type: 'service_health', title: 'Service Health', datasource: 'prometheus', limit: 5 },
  { widget_id: 'telemetry-summary', type: 'telemetry_summary', title: 'Telemetry Coverage', datasource: 'prometheus', limit: 4 },
];

const primaryTypes = new Set(['findings_table', 'risky_assets', 'vulnerabilities_summary', 'service_health']);

function normalizeDraftWidgets(widgets: Array<Record<string, unknown>>): DraftWidget[] {
  if (!Array.isArray(widgets) || widgets.length === 0) {
    return defaultWidgets;
  }
  return widgets.slice(0, 8).map((widget, index) => ({
    widget_id: String(widget.widget_id ?? `${String(widget.type ?? 'widget')}-${index}`),
    type: String(widget.type ?? 'metric_card'),
    title: String(widget.title ?? 'Untitled Widget'),
    datasource: String(widget.datasource ?? ''),
    limit: typeof widget.limit === 'number' ? widget.limit : 5,
  }));
}

function createDraftWidget(definition: WidgetDefinition): DraftWidget {
  return {
    widget_id: `${definition.type}-${Math.random().toString(36).slice(2, 8)}`,
    type: definition.type,
    title: definition.label,
    datasource: '',
    limit: definition.type === 'metric_card' ? 1 : 5,
  };
}

function groupWidgets(widgets: RenderedWidget[]) {
  const visibleWidgets = widgets.slice(0, 8);
  return {
    metrics: visibleWidgets.filter((widget) => widget.type === 'metric_card').slice(0, 3),
    primary: visibleWidgets.filter((widget) => primaryTypes.has(widget.type)).slice(0, 3),
    secondary: visibleWidgets.filter((widget) => !primaryTypes.has(widget.type) && widget.type !== 'metric_card').slice(0, 2),
  };
}

export function Dashboards({ selectedEnvironmentId, dashboards, datasources, loading, error, onDataChanged }: DashboardsProps) {
  const [selectedDashboardId, setSelectedDashboardId] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [widgets, setWidgets] = useState<DraftWidget[]>(defaultWidgets);
  const [showSelector, setShowSelector] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const visibleDashboards = useMemo(
    () => dashboards.filter((dashboard) => dashboard.environment_id === selectedEnvironmentId),
    [dashboards, selectedEnvironmentId],
  );
  const activeDashboard = visibleDashboards.find((dashboard) => dashboard.dashboard_id === selectedDashboardId) ?? visibleDashboards[0] ?? null;
  const renderFetch = useFetch(() => (activeDashboard ? getRenderedDashboard(activeDashboard.dashboard_id) : Promise.resolve(null)), [activeDashboard?.dashboard_id]);
  const environmentDatasources = useMemo(
    () => datasources.filter((datasource) => datasource.environment_id === selectedEnvironmentId),
    [datasources, selectedEnvironmentId],
  );
  const groupedWidgets = useMemo(() => groupWidgets(renderFetch.data?.widgets ?? []), [renderFetch.data?.widgets]);

  useEffect(() => {
    if (!activeDashboard) {
      setName('');
      setDescription('');
      setWidgets(defaultWidgets);
      return;
    }
    setSelectedDashboardId(activeDashboard.dashboard_id);
    setName(activeDashboard.name);
    setDescription(activeDashboard.description ?? '');
    setWidgets(normalizeDraftWidgets(activeDashboard.widgets));
  }, [activeDashboard]);

  async function handleSave() {
    setSaving(true);
    setActionError(null);
    try {
      const payload = {
        environment_id: selectedEnvironmentId,
        name: name.trim() || 'Dashboard',
        description: description.trim() || null,
        layout: { columns: 12, rowHeight: 96 },
        widgets: widgets.slice(0, 8).map((widget) => ({
          widget_id: widget.widget_id,
          type: widget.type,
          title: widget.title,
          datasource: widget.datasource || undefined,
          limit: widget.limit,
        })),
      };
      if (activeDashboard) {
        await updateDashboard(activeDashboard.dashboard_id, {
          name: payload.name,
          description: payload.description,
          layout: payload.layout,
          widgets: payload.widgets,
        });
      } else {
        await createDashboard(payload);
      }
      onDataChanged();
      setIsEditing(false);
      void renderFetch.refetch();
    } catch (errorValue) {
      setActionError(errorValue instanceof Error ? errorValue.message : 'Unable to save dashboard');
    } finally {
      setSaving(false);
    }
  }

  function renderSection(title: string, descriptionText: string, items: RenderedWidget[], variant: 'kpi' | 'primary' | 'secondary') {
    if (!items.length) {
      return null;
    }
    return (
      <section className="space-y-4">
        <SectionHeader title={title} description={descriptionText} />
        <DashboardGrid variant={variant}>
          {items.map((widget, index) => (
            <div key={`${widget.type}-${widget.widget_id ?? index}`}>{renderDashboardWidget(widget)}</div>
          ))}
        </DashboardGrid>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <WidgetSelectorModal open={showSelector} definitions={widgetDefinitions} onClose={() => setShowSelector(false)} onSelect={(definition) => {
        if (widgets.length >= 8) {
          return;
        }
        setWidgets((current) => [...current, createDraftWidget(definition)]);
        setShowSelector(false);
      }} />

      {(error || actionError) ? <div className="theme-error rounded-2xl p-4 text-sm">{error ?? actionError}</div> : null}

      <Panel
        title="Dashboards"
        eyebrow="Reduced Workspace"
        description="Dashboards are capped to a small set of primary widgets so the page stays readable."
        action={
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge label={`${Math.min(widgets.length, 8)}/8 widgets`} tone="slate" />
            <button type="button" onClick={() => setIsEditing((current) => !current)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
              {isEditing ? 'Close Editor' : 'Edit Layout'}
            </button>
          </div>
        }
      >
        <div className="grid gap-4 lg:grid-cols-[1fr,auto] lg:items-center">
          <label className="grid gap-2">
            <span className="theme-text-faint text-[11px] font-semibold uppercase tracking-[0.18em]">Active Dashboard</span>
            <select
              value={activeDashboard?.dashboard_id ?? ''}
              onChange={(event) => setSelectedDashboardId(event.target.value)}
              className="theme-input theme-focus rounded-2xl border px-4 py-3"
            >
              {visibleDashboards.map((dashboard) => (
                <option key={dashboard.dashboard_id} value={dashboard.dashboard_id}>
                  {dashboard.name}
                </option>
              ))}
              {!visibleDashboards.length ? <option value="">No dashboards yet</option> : null}
            </select>
          </label>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => {
                setSelectedDashboardId('');
                setName('New Dashboard');
                setDescription('');
                setWidgets(defaultWidgets);
                setIsEditing(true);
              }}
              className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold transition"
            >
              New Dashboard
            </button>
            <button type="button" onClick={() => void renderFetch.refetch()} className="theme-button-secondary rounded-2xl px-4 py-3 text-sm font-semibold transition">
              Refresh
            </button>
          </div>
        </div>
      </Panel>

      {isEditing ? (
        <Panel title="Dashboard Editor" description="Keep the layout to six to eight widgets and prioritize the sections that matter most.">
          <div className="grid gap-4">
            <input className="theme-input theme-focus rounded-2xl border px-4 py-3" value={name} onChange={(event) => setName(event.target.value)} placeholder="Dashboard name" />
            <textarea
              className="theme-input theme-focus min-h-24 rounded-2xl border px-4 py-3"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Short description"
            />

            <div className="space-y-3">
              {widgets.slice(0, 8).map((widget, index) => (
                <div key={widget.widget_id} className="theme-inset grid gap-3 rounded-2xl border p-4 lg:grid-cols-[1.2fr,1fr,90px,auto] lg:items-center">
                  <input
                    className="theme-input theme-focus rounded-2xl border px-4 py-3"
                    value={widget.title}
                    onChange={(event) => setWidgets((current) => current.map((item) => (item.widget_id === widget.widget_id ? { ...item, title: event.target.value } : item)))}
                  />
                  <select
                    className="theme-input theme-focus rounded-2xl border px-4 py-3"
                    value={widget.datasource}
                    onChange={(event) => setWidgets((current) => current.map((item) => (item.widget_id === widget.widget_id ? { ...item, datasource: event.target.value } : item)))}
                  >
                    <option value="">Auto</option>
                    {environmentDatasources.map((datasource) => (
                      <option key={datasource.datasource_id} value={datasource.datasource_id}>
                        {datasource.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    className="theme-input theme-focus rounded-2xl border px-4 py-3"
                    value={widget.limit}
                    onChange={(event) => setWidgets((current) => current.map((item) => (item.widget_id === widget.widget_id ? { ...item, limit: Number(event.target.value) } : item)))}
                  />
                  <div className="flex gap-2">
                    <button type="button" onClick={() => setWidgets((current) => current.filter((item) => item.widget_id !== widget.widget_id))} className="theme-button-secondary rounded-2xl px-3 py-2 text-sm font-semibold transition">
                      Remove
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setWidgets((current) => {
                          if (index === 0) {
                            return current;
                          }
                          const next = [...current];
                          [next[index - 1], next[index]] = [next[index], next[index - 1]];
                          return next;
                        })
                      }
                      className="theme-button-secondary rounded-2xl px-3 py-2 text-sm font-semibold transition"
                    >
                      Up
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <button type="button" onClick={() => setShowSelector(true)} disabled={widgets.length >= 8} className="theme-button-secondary rounded-2xl px-4 py-3 text-sm font-semibold transition disabled:opacity-40">
                Add Widget
              </button>
              <button type="button" onClick={() => void handleSave()} disabled={saving} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold transition disabled:opacity-60">
                {saving ? 'Saving...' : 'Save Dashboard'}
              </button>
            </div>
          </div>
        </Panel>
      ) : null}

      {loading || renderFetch.loading ? <WidgetLoadingState /> : null}

      {!loading && !renderFetch.loading && !renderFetch.data ? (
        <div className="space-y-4">
          <WidgetEmptyState message="No dashboard selected yet. Create one to populate this environment with a focused set of widgets." />
          <button type="button" onClick={() => setIsEditing(true)} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold transition">
            Create Dashboard
          </button>
        </div>
      ) : null}

      {!loading && renderFetch.data ? (
        <div className="space-y-6">
          {renderSection('Primary Metrics', 'Keep the top row small and immediately scannable.', groupedWidgets.metrics, 'kpi')}
          {renderSection('Operational Focus', 'This section carries the main analyst workflow.', groupedWidgets.primary, 'primary')}
          {renderSection('Supporting Context', 'Secondary context stays below the primary views.', groupedWidgets.secondary, 'secondary')}
        </div>
      ) : null}
    </div>
  );
}
