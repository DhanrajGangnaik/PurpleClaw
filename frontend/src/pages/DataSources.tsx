import { useMemo, useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { JsonPanel } from '../components/JsonPanel';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { createDatasource, testDatasource } from '../services/api';
import type { RegisteredDataSource } from '../types/api';
import { formatDate } from '../utils';

interface DataSourcesProps {
  selectedEnvironmentId: string;
  datasources: RegisteredDataSource[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

const defaultConfigs: Record<RegisteredDataSource['type'], string> = {
  prometheus: JSON.stringify({ url: 'http://localhost:9090', timeout_seconds: 2 }, null, 2),
  loki: JSON.stringify({ url: 'http://localhost:3100', timeout_seconds: 2 }, null, 2),
  file: JSON.stringify({ path: 'reports/example.json' }, null, 2),
  api: JSON.stringify({ url: 'https://api.internal.example/v1', timeout_seconds: 2 }, null, 2),
  inventory: JSON.stringify({ managed: true }, null, 2),
  scanner_results: JSON.stringify({ managed: true }, null, 2),
};

function tone(status: RegisteredDataSource['status']) {
  if (status === 'enabled') {
    return 'green';
  }
  if (status === 'error') {
    return 'red';
  }
  return 'slate';
}

export function DataSources({ selectedEnvironmentId, datasources, loading, error, onDataChanged }: DataSourcesProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState<RegisteredDataSource['type']>('api');
  const [status, setStatus] = useState<RegisteredDataSource['status']>('enabled');
  const [configText, setConfigText] = useState(defaultConfigs.api);
  const [actionError, setActionError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ message: string; ok: boolean } | null>(null);
  const [saving, setSaving] = useState(false);
  const [selectedSourceId, setSelectedSourceId] = useState('');

  const visibleDataSources = useMemo(
    () => datasources.filter((item) => item.environment_id === selectedEnvironmentId),
    [datasources, selectedEnvironmentId],
  );
  const selectedSource = visibleDataSources.find((item) => item.datasource_id === selectedSourceId) ?? visibleDataSources[0] ?? null;
  const ingestionEnabled = visibleDataSources.filter((item) => item.ingestion_enabled).length;

  const columns: DataColumn<RegisteredDataSource>[] = [
    { key: 'name', label: 'Data Source', render: (item) => <span className="theme-text-primary font-medium">{item.name}</span> },
    { key: 'type', label: 'Type', render: (item) => <StatusBadge label={item.type} tone="purple" /> },
    { key: 'status', label: 'Status', render: (item) => <StatusBadge label={item.status} tone={tone(item.status)} /> },
    { key: 'ingestion', label: 'Ingestion', render: (item) => <StatusBadge label={item.ingestion_enabled ? 'enabled' : 'manual'} tone={item.ingestion_enabled ? 'green' : 'slate'} /> },
    { key: 'updated', label: 'Updated', render: (item) => formatDate(item.updated_at) },
    { key: 'tested', label: 'Last Tested', render: (item) => formatDate(item.last_tested_at ?? undefined) },
  ];

  const parseConfig = () => JSON.parse(configText) as Record<string, unknown>;

  const handleSave = async () => {
    setSaving(true);
    setActionError(null);
    setTestResult(null);
    try {
      await createDatasource({
        environment_id: selectedEnvironmentId,
        name,
        type,
        status,
        config: parseConfig(),
      });
      setName('');
      onDataChanged();
    } catch (actionValue) {
      setActionError(actionValue instanceof Error ? actionValue.message : 'Unable to register data source');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setSaving(true);
    setActionError(null);
    try {
      const result = await testDatasource({
        environment_id: selectedEnvironmentId,
        type,
        config: parseConfig(),
      });
      setTestResult({ ok: result.ok, message: result.message });
    } catch (actionValue) {
      setActionError(actionValue instanceof Error ? actionValue.message : 'Unable to test data source');
    } finally {
      setSaving(false);
    }
  };

  if (!selectedEnvironmentId) {
    return (
      <Panel title="Data Sources" eyebrow="Environment Required">
        <div className="theme-text-faint py-12 text-center text-sm">Create an environment before adding data sources.</div>
      </Panel>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
        <Panel title="Register Data Sources" eyebrow="Connector Setup" description="Register telemetry, inventory, or scanner feeds for the active environment. Functional registration and test flows are unchanged.">
          {(error || actionError) ? <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error ?? actionError}</div> : null}
          {testResult ? (
            <div className={`mb-4 rounded-2xl border p-4 text-sm ${testResult.ok ? 'theme-button-secondary' : 'theme-error'}`}>
              {testResult.message}
            </div>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-2">
            <label className="space-y-2">
              <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Name</span>
              <input value={name} onChange={(event) => setName(event.target.value)} className="theme-input theme-focus rounded-2xl px-4 py-3" placeholder="Prometheus West" />
            </label>
            <label className="space-y-2">
              <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Type</span>
              <select
                value={type}
                onChange={(event) => {
                  const nextType = event.target.value as RegisteredDataSource['type'];
                  setType(nextType);
                  setConfigText(defaultConfigs[nextType]);
                }}
                className="theme-input theme-focus rounded-2xl px-4 py-3"
              >
                {Object.keys(defaultConfigs).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2">
              <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Status</span>
              <select value={status} onChange={(event) => setStatus(event.target.value as RegisteredDataSource['status'])} className="theme-input theme-focus rounded-2xl px-4 py-3">
                <option value="enabled">enabled</option>
                <option value="disabled">disabled</option>
                <option value="error">error</option>
              </select>
            </label>
            <div className="theme-inset rounded-2xl p-4">
              <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Boundaries</p>
              <p className="theme-text-muted mt-2 text-sm leading-6">
                Connection tests are environment-scoped and limited to safe metadata validation. Secret fields are masked and not echoed back in logs.
              </p>
            </div>
          </div>

          <label className="mt-4 block space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Config JSON</span>
            <textarea value={configText} onChange={(event) => setConfigText(event.target.value)} className="theme-input theme-focus min-h-48 rounded-2xl px-4 py-3 font-mono text-sm" />
          </label>

          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" onClick={handleTest} disabled={saving} className="theme-button-secondary rounded-2xl px-4 py-3 text-sm font-semibold">
              {saving ? 'Testing...' : 'Test Connection'}
            </button>
            <button type="button" onClick={handleSave} disabled={saving || !name.trim()} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold">
              {saving ? 'Saving...' : 'Register Data Source'}
            </button>
          </div>
        </Panel>

        <Panel title="Ingestion Status" eyebrow="Operational Health" description="A compact view of connector readiness and selected source metadata.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            <div className="workspace-stat">
              <p className="workspace-eyebrow">Registered</p>
              <p className="mt-3 text-3xl font-semibold" style={{ color: 'var(--text-primary)' }}>{visibleDataSources.length}</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Total connectors in this environment</p>
            </div>
            <div className="workspace-stat">
              <p className="workspace-eyebrow">Ingestion Enabled</p>
              <p className="mt-3 text-3xl font-semibold" style={{ color: 'var(--text-primary)' }}>{ingestionEnabled}</p>
              <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>Sources configured for scheduled ingestion</p>
            </div>
            <div className="workspace-subpanel p-4">
              <p className="workspace-eyebrow">Selected Source</p>
              {selectedSource ? (
                <div className="mt-3 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge label={selectedSource.type} tone="purple" />
                    <StatusBadge label={selectedSource.status} tone={tone(selectedSource.status)} />
                  </div>
                  <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selectedSource.name}</p>
                  <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                    Updated {formatDate(selectedSource.updated_at)} · Last tested {formatDate(selectedSource.last_tested_at ?? undefined)}
                  </p>
                </div>
              ) : (
                <p className="mt-3 text-sm" style={{ color: 'var(--text-muted)' }}>No source selected yet.</p>
              )}
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Registered Sources" eyebrow="Connected Inputs" description="Click any row to inspect the selected connector without dropping into a raw JSON-first workflow.">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading environment data sources...</div>
        ) : (
          <DataTable columns={columns} rows={visibleDataSources} getRowKey={(item) => item.datasource_id} emptyText="No data sources registered for this environment." onRowClick={(item) => setSelectedSourceId(item.datasource_id)} />
        )}
      </Panel>

      <div className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
        <Panel title="Selected Source Preview" eyebrow="Configuration">
          {selectedSource ? (
            <div className="space-y-3">
              <div className="workspace-subpanel p-4">
                <p className="workspace-eyebrow">Connector Details</p>
                <p className="mt-3 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{selectedSource.name}</p>
                <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
                  Type {selectedSource.type} · Interval {selectedSource.ingestion_interval_seconds ? `${selectedSource.ingestion_interval_seconds}s` : 'manual'}
                </p>
              </div>
              <JsonPanel value={selectedSource.config} emptyText="No source config available." />
            </div>
          ) : (
            <div className="theme-text-faint py-14 text-center text-sm">Select a source from the table to inspect its configuration.</div>
          )}
        </Panel>
        <Panel title="Configuration Inventory" eyebrow="Advanced View" description="Full raw output remains available for troubleshooting and advanced operator review.">
          <JsonPanel value={visibleDataSources} emptyText="No data sources available for preview." />
        </Panel>
      </div>
    </div>
  );
}
