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
  const visibleDataSources = useMemo(
    () => datasources.filter((item) => item.environment_id === selectedEnvironmentId),
    [datasources, selectedEnvironmentId],
  );

  const columns: DataColumn<RegisteredDataSource>[] = [
    { key: 'name', label: 'Data Source', render: (item) => <span className="theme-text-primary font-medium">{item.name}</span> },
    { key: 'type', label: 'Type', render: (item) => <StatusBadge label={item.type} tone="purple" /> },
    { key: 'status', label: 'Status', render: (item) => <StatusBadge label={item.status} tone={tone(item.status)} /> },
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

  return (
    <div className="space-y-6">
      <Panel title="Register Data Sources" eyebrow="Environment Scoped">
        {(error || actionError) && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error ?? actionError}</div>}
        {testResult && (
          <div className={`mb-4 rounded-2xl border p-4 text-sm ${testResult.ok ? 'theme-button-secondary' : 'theme-error'}`}>
            {testResult.message}
          </div>
        )}
        <div className="grid gap-4 lg:grid-cols-2">
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Name</span>
            <input value={name} onChange={(event) => setName(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3" placeholder="Prometheus West" />
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
              className="theme-input theme-focus w-full rounded-2xl border px-4 py-3"
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
            <select value={status} onChange={(event) => setStatus(event.target.value as RegisteredDataSource['status'])} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3">
              <option value="enabled">enabled</option>
              <option value="disabled">disabled</option>
              <option value="error">error</option>
            </select>
          </label>
          <div className="theme-inset rounded-2xl border p-4">
            <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Boundaries</p>
            <p className="theme-text-muted mt-2 text-sm leading-6">
              Connection tests are environment-scoped and limited to safe metadata validation. Secret fields are masked and not echoed back in logs.
            </p>
          </div>
        </div>
        <label className="mt-4 block space-y-2">
          <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Config JSON</span>
          <textarea value={configText} onChange={(event) => setConfigText(event.target.value)} className="theme-input theme-focus min-h-48 w-full rounded-2xl border px-4 py-3 font-mono text-sm" />
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

      <Panel title="Registered Sources" eyebrow="Connected Inputs">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading environment data sources...</div>
        ) : (
          <DataTable columns={columns} rows={visibleDataSources} getRowKey={(item) => item.datasource_id} emptyText="No data sources registered for this environment." />
        )}
      </Panel>

      <Panel title="Selected Configuration" eyebrow="Preview">
        <JsonPanel value={visibleDataSources} emptyText="No data sources available for preview." />
      </Panel>
    </div>
  );
}
