import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard } from '../../components/ui';
import { getEngineStatus, triggerScan } from '../../services/api';
import { Cpu, RefreshCw, Play, Wifi, WifiOff, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

type RegistryEntry = {
  url?: string;
  type?: string;
  status?: string;
  name?: string;
  last_check?: string;
};

type EngineStatus = {
  scan_network_enabled?: boolean;
  auto_response_enabled?: boolean;
  auto_response_level?: string;
  assets_discovered?: number;
  open_alerts?: number;
  open_findings?: number;
  open_incidents?: number;
  discovery_job?: { next_run?: string; last_run?: string; status?: string } | null;
  threat_job?: { next_run?: string; last_run?: string; status?: string } | null;
  registry?: Record<string, RegistryEntry>;
};

const statusColor = (s?: string) =>
  s === 'confirmed' ? 'text-green-400' :
  s === 'discovered' ? 'text-blue-400' :
  s === 'unreachable' ? 'text-red-400' : 'text-gray-500';

const statusDot = (s?: string) =>
  s === 'confirmed' ? 'bg-green-500' :
  s === 'discovered' ? 'bg-blue-500' :
  s === 'unreachable' ? 'bg-red-500' : 'bg-gray-600';

export function Engine() {
  const [status, setStatus] = useState<EngineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const load = () => {
    setLoading(true);
    getEngineStatus()
      .then((s) => setStatus(s as EngineStatus))
      .catch(() => toast.error('Failed to load engine status'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const trigger = async () => {
    setScanning(true);
    try {
      const r = await triggerScan('both') as { triggered?: string[]; error?: string };
      if (r.error) toast.error(`Scan error: ${r.error}`);
      else toast.success(`Triggered: ${(r.triggered ?? []).join(', ')}`);
      setTimeout(load, 2000);
    } catch { toast.error('Failed to trigger scan'); }
    finally { setScanning(false); }
  };

  const registry = status?.registry ?? {};
  const registryEntries = Object.entries(registry);
  const confirmed = registryEntries.filter(([, v]) => v.status === 'confirmed').length;
  const discovered = registryEntries.filter(([, v]) => v.status === 'discovered').length;
  const unreachable = registryEntries.filter(([, v]) => v.status === 'unreachable').length;

  return (
    <Layout title="Engine Status">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Assets Discovered" value={status?.assets_discovered ?? 0} color="blue" />
          <MetricCard label="Services Confirmed" value={confirmed} color="green" />
          <MetricCard label="Unreachable" value={unreachable} color="red" />
          <MetricCard label="Open Alerts" value={status?.open_alerts ?? 0} color="orange" />
        </div>

        {/* Engine controls */}
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-4">
            <Cpu className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Autonomous Engine</h2>
            <div className="ml-auto flex gap-2">
              <button onClick={load} className="btn-secondary p-2"><RefreshCw className="w-4 h-4" /></button>
              <button onClick={trigger} disabled={scanning} className="btn-primary flex items-center gap-2">
                <Play className="w-4 h-4" />{scanning ? 'Triggering…' : 'Trigger Scan Now'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Discovery job */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <p className="text-xs font-semibold text-gray-400 mb-2">Discovery Engine</p>
              <div className="flex items-center gap-2 mb-1">
                <div className={`w-2 h-2 rounded-full ${status?.discovery_job ? 'bg-green-500' : 'bg-gray-600'}`} />
                <span className="text-xs text-gray-300">{status?.discovery_job ? 'Running' : 'Idle'}</span>
              </div>
              {status?.discovery_job?.last_run && (
                <p className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3" /> Last: {new Date(status.discovery_job.last_run).toLocaleString()}
                </p>
              )}
              {status?.discovery_job?.next_run && (
                <p className="text-xs text-gray-600 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Next: {new Date(status.discovery_job.next_run).toLocaleString()}
                </p>
              )}
            </div>

            {/* Threat engine */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <p className="text-xs font-semibold text-gray-400 mb-2">Threat Engine</p>
              <div className="flex items-center gap-2 mb-1">
                <div className={`w-2 h-2 rounded-full ${status?.threat_job ? 'bg-green-500' : 'bg-gray-600'}`} />
                <span className="text-xs text-gray-300">{status?.threat_job ? 'Running' : 'Idle'}</span>
              </div>
              {status?.threat_job?.last_run && (
                <p className="text-xs text-gray-600 flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3" /> Last: {new Date(status.threat_job.last_run).toLocaleString()}
                </p>
              )}
            </div>

            {/* Auto response */}
            <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <p className="text-xs font-semibold text-gray-400 mb-2">Auto Response</p>
              <div className="flex items-center gap-2">
                {status?.auto_response_enabled
                  ? <Wifi className="w-4 h-4 text-green-400" />
                  : <WifiOff className="w-4 h-4 text-gray-600" />}
                <span className="text-xs text-gray-300">{status?.auto_response_enabled ? 'Enabled' : 'Disabled'}</span>
              </div>
              {status?.auto_response_level && (
                <p className="text-xs text-gray-600 mt-1">Level: {status.auto_response_level}</p>
              )}
              <p className="text-xs text-gray-600 mt-1">
                Network scan: {status?.scan_network_enabled ? 'on' : 'off'}
              </p>
            </div>
          </div>
        </div>

        {/* Service registry */}
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Service Registry</h2>
            <span className="ml-2 text-xs text-gray-600">{registryEntries.length} services · {confirmed} confirmed · {discovered} discovered · {unreachable} unreachable</span>
          </div>

          {loading ? <PageLoading /> : registryEntries.length === 0 ? (
            <div className="p-8 text-center text-sm text-gray-600">No services in registry. Trigger a scan to discover services.</div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name / ID</th><th>Type</th><th>URL</th><th>Status</th><th>Last Check</th></tr></thead>
                <tbody>
                  {registryEntries.map(([id, svc]) => (
                    <tr key={id}>
                      <td className="font-medium text-gray-200 text-sm">{svc.name ?? id}</td>
                      <td><span className="badge badge-info">{svc.type ?? '—'}</span></td>
                      <td className="font-mono text-xs text-gray-500 max-w-xs truncate">{svc.url ?? '—'}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${statusDot(svc.status)}`} />
                          <span className={`text-xs font-medium ${statusColor(svc.status)}`}>{svc.status ?? 'unknown'}</span>
                        </div>
                      </td>
                      <td className="text-gray-600 text-xs">
                        {svc.last_check ? new Date(svc.last_check).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
