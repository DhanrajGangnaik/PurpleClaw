import { useEffect, useMemo, useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { JsonPanel } from '../components/JsonPanel';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { runScan } from '../services/api';
import type { ScanDetail, ScanPolicy } from '../types/api';
import { formatDate, shortId } from '../utils';

interface ScansProps {
  selectedEnvironmentId: string;
  policies: ScanPolicy[];
  scans: ScanDetail[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

const availableScanTypes = [
  'inventory_match',
  'tls_check',
  'service_detection',
  'header_analysis',
  'config_audit',
  'exposure_review',
  'telemetry_gap_check',
] as const;

function tone(status: string) {
  if (status === 'completed' || status === 'ready') {
    return 'green';
  }
  if (status === 'blocked' || status === 'failed') {
    return 'red';
  }
  if (status === 'running') {
    return 'cyan';
  }
  return 'slate';
}

export function Scans({ selectedEnvironmentId, policies, scans, loading, error, onDataChanged }: ScansProps) {
  const [target, setTarget] = useState('');
  const [targetType, setTargetType] = useState<'asset' | 'hostname' | 'ip' | 'service'>('asset');
  const [depth, setDepth] = useState<'light' | 'standard'>('light');
  const [requestedBy, setRequestedBy] = useState('');
  const [notes, setNotes] = useState('');
  const [selectedScanTypes, setSelectedScanTypes] = useState<string[]>(['inventory_match', 'telemetry_gap_check']);
  const [latestResult, setLatestResult] = useState<ScanDetail | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const visiblePolicies = useMemo(
    () => policies.filter((item) => item.environment_id === selectedEnvironmentId),
    [policies, selectedEnvironmentId],
  );
  const activePolicy = visiblePolicies.find((item) => item.enabled) ?? null;
  const visibleScans = useMemo(
    () => scans.filter((item) => item.request.environment_id === selectedEnvironmentId),
    [scans, selectedEnvironmentId],
  );

  useEffect(() => {
    const activeScan = visibleScans.some((item) => ['queued', 'running'].includes(item.result?.status ?? item.request.status));
    if (!activeScan) {
      return;
    }
    const timer = window.setInterval(() => {
      onDataChanged();
    }, 3000);
    return () => window.clearInterval(timer);
  }, [onDataChanged, visibleScans]);

  useEffect(() => {
    if (!latestResult) {
      return;
    }
    const refreshed = visibleScans.find((item) => item.request.scan_id === latestResult.request.scan_id);
    if (refreshed) {
      setLatestResult(refreshed);
    }
  }, [latestResult, visibleScans]);

  const scanColumns: DataColumn<ScanDetail>[] = [
    { key: 'target', label: 'Target', render: (item) => <span className="theme-text-primary font-medium">{item.request.target}</span> },
    { key: 'type', label: 'Type', render: (item) => <StatusBadge label={item.request.target_type} tone="purple" /> },
    { key: 'status', label: 'Status', render: (item) => <StatusBadge label={item.result?.status ?? item.request.status} tone={tone(item.result?.status ?? item.request.status)} /> },
    { key: 'checks', label: 'Checks', render: (item) => shortId(item.request.scan_types.join(', '), 28) },
    { key: 'findings', label: 'Findings', render: (item) => item.result?.findings_created ?? 0 },
    { key: 'requested', label: 'Requested', render: (item) => formatDate(item.request.requested_at) },
  ];

  const handleToggle = (scanType: string) => {
    setSelectedScanTypes((current) => (current.includes(scanType) ? current.filter((item) => item !== scanType) : [...current, scanType]));
  };

  const handleRun = async () => {
    setRunning(true);
    setActionError(null);
    try {
      const result = await runScan({
        environment_id: selectedEnvironmentId,
        target,
        target_type: targetType,
        scan_types: selectedScanTypes,
        depth,
        requested_by: requestedBy || null,
        notes: notes || null,
      });
      setLatestResult(result);
      onDataChanged();
      if (result.result?.status === 'blocked') {
        setActionError(String(result.result.summary.message ?? 'Target is blocked by policy'));
      }
    } catch (actionValue) {
      setActionError(actionValue instanceof Error ? actionValue.message : 'Unable to run scan');
    } finally {
      setRunning(false);
    }
  };

  const generatedFindings = Array.isArray(latestResult?.result?.summary.generated_findings)
    ? (latestResult?.result?.summary.generated_findings as Array<Record<string, unknown>>)
    : [];

  return (
    <div className="space-y-6">
      <Panel title="Controlled Assessment Run" eyebrow="Approved Scope Only">
        {(error || actionError) && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error ?? actionError}</div>}
        <div className="grid gap-4 xl:grid-cols-2">
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Target</span>
            <input value={target} onChange={(event) => setTarget(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3" placeholder="asset-001 or edge-gateway-01" />
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Target Type</span>
            <select value={targetType} onChange={(event) => setTargetType(event.target.value as 'asset' | 'hostname' | 'ip' | 'service')} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3">
              <option value="asset">asset</option>
              <option value="hostname">hostname</option>
              <option value="ip">ip</option>
              <option value="service">service</option>
            </select>
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Depth</span>
            <select value={depth} onChange={(event) => setDepth(event.target.value as 'light' | 'standard')} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3">
              <option value="light">light</option>
              <option value="standard">standard</option>
            </select>
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Requested By</span>
            <input value={requestedBy} onChange={(event) => setRequestedBy(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3" placeholder="analyst@purpleclaw.local" />
          </label>
        </div>
        <label className="mt-4 block space-y-2">
          <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Notes</span>
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} className="theme-input theme-focus min-h-24 w-full rounded-2xl border px-4 py-3" placeholder="Reason for the approved assessment request." />
        </label>
        <div className="mt-4">
          <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Scan Types</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {availableScanTypes.map((scanType) => (
              <label key={scanType} className="theme-inset flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm">
                <input type="checkbox" checked={selectedScanTypes.includes(scanType)} onChange={() => handleToggle(scanType)} />
                <span>{scanType}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" onClick={handleRun} disabled={running || !target.trim() || selectedScanTypes.length === 0} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold">
            {running ? 'Running...' : 'Run Scan'}
          </button>
          {activePolicy && <StatusBadge label={`Policy ${activePolicy.max_depth}`} tone="cyan" />}
        </div>
      </Panel>

      <Panel title="Scope Controls" eyebrow="Policy Enforcement">
        {activePolicy ? (
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="theme-inset rounded-2xl border p-4">
              <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Allowed Targets</p>
              <p className="theme-text-muted mt-3 text-sm leading-6">{activePolicy.allowed_targets.join(', ') || 'No explicit targets'}</p>
            </div>
            <div className="theme-inset rounded-2xl border p-4">
              <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Allowed Network Ranges</p>
              <p className="theme-text-muted mt-3 text-sm leading-6">{activePolicy.allowed_network_ranges.join(', ') || 'No IP ranges approved'}</p>
            </div>
            <div className="theme-inset rounded-2xl border p-4">
              <p className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Approved Checks</p>
              <p className="theme-text-muted mt-3 text-sm leading-6">{activePolicy.allowed_scan_types.join(', ')}</p>
            </div>
          </div>
        ) : (
          <div className="theme-text-faint py-12 text-center text-sm">No enabled scan policy is available for this environment.</div>
        )}
      </Panel>

      <Panel title="Latest Result" eyebrow="Assessment Outcome">
        {latestResult ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusBadge label={latestResult.result?.status ?? latestResult.request.status} tone={tone(latestResult.result?.status ?? latestResult.request.status)} />
              <span className="theme-text-primary font-medium">{latestResult.request.target}</span>
              <span className="theme-text-muted text-sm">{latestResult.result?.findings_created ?? 0} findings created</span>
            </div>
            <JsonPanel value={latestResult.result?.summary ?? latestResult} emptyText="No scan result available yet." />
            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Generated Findings" eyebrow="Summary" className="p-0">
                <div className="space-y-3">
                  {generatedFindings.length === 0 ? (
                    <div className="theme-text-faint text-sm">No generated findings for the latest run.</div>
                  ) : (
                    generatedFindings.map((item) => (
                      <div key={`${item.title}-${item.score}`} className="theme-inset rounded-2xl border p-4">
                        <div className="flex items-center gap-3">
                          <StatusBadge label={String(item.severity)} tone={String(item.severity) === 'high' ? 'red' : String(item.severity) === 'medium' ? 'purple' : 'cyan'} />
                          <span className="theme-text-primary font-medium">{String(item.title)}</span>
                        </div>
                        <p className="theme-text-muted mt-2 text-sm leading-6">{String(item.evidence_summary ?? '')}</p>
                      </div>
                    ))
                  )}
                </div>
              </Panel>
              <Panel title="Related Findings" eyebrow="Existing Context" className="p-0">
                <div className="space-y-3">
                  {latestResult.related_findings.length === 0 ? (
                    <div className="theme-text-faint text-sm">No related findings were mapped for this target.</div>
                  ) : (
                    latestResult.related_findings.map((item) => (
                      <div key={item.id} className="theme-inset rounded-2xl border p-4">
                        <div className="flex items-center gap-3">
                          <StatusBadge label={item.severity} tone={item.severity === 'critical' || item.severity === 'high' ? 'red' : item.severity === 'medium' ? 'purple' : 'cyan'} />
                          <span className="theme-text-primary font-medium">{item.title}</span>
                        </div>
                        <p className="theme-text-muted mt-2 text-sm">Risk Score {item.score} - {item.status}</p>
                      </div>
                    ))
                  )}
                </div>
              </Panel>
            </div>
          </div>
        ) : (
          <div className="theme-text-faint py-14 text-center text-sm">Run an approved assessment to see scan status, findings created, summary, and related findings.</div>
        )}
      </Panel>

      <Panel title="Recent Assessments" eyebrow="Run History">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading assessment history...</div>
        ) : (
          <DataTable columns={scanColumns} rows={visibleScans} getRowKey={(item) => item.request.scan_id} emptyText="No approved assessment runs have been recorded for this environment." onRowClick={setLatestResult} />
        )}
      </Panel>
    </div>
  );
}
