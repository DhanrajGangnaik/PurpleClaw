import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, SeverityBadge, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getAlerts, updateAlert } from '../../services/api';
import type { Alert, Paginated } from '../../services/api';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

export function Alerts() {
  const [data, setData] = useState<Paginated<Alert> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const load = () => {
    setLoading(true);
    getAlerts(page, 25, statusFilter || undefined, severityFilter || undefined)
      .then(setData).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [page, severityFilter, statusFilter]);

  const acknowledge = async (id: number) => {
    await updateAlert(id, { status: 'investigating' });
    toast.success('Alert acknowledged');
    load();
  };

  const close = async (id: number) => {
    await updateAlert(id, { status: 'closed' });
    toast.success('Alert closed');
    load();
  };

  const stats = data?.items ?? [];
  const critical = stats.filter((a) => a.severity === 'critical').length;
  const high = stats.filter((a) => a.severity === 'high').length;
  const open = stats.filter((a) => a.status === 'open').length;

  return (
    <Layout title="Alerts">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Alerts" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Critical" value={critical} color="red" />
          <MetricCard label="High" value={high} color="orange" />
          <MetricCard label="Open" value={open} color="blue" />
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-3 flex-wrap">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            <h2 className="text-sm font-semibold text-gray-300">Security Alerts</h2>
            <div className="ml-auto flex items-center gap-2 flex-wrap">
              <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="w-36">
                <option value="">All Severities</option>
                {['critical','high','medium','low'].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="w-36">
                <option value="">All Statuses</option>
                {['open','investigating','closed','false_positive'].map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
              <button onClick={load} className="btn-secondary p-2"><RefreshCw className="w-4 h-4" /></button>
            </div>
          </div>

          {loading ? <PageLoading /> : (
            data?.items.length === 0 ? <EmptyState icon={<AlertTriangle className="w-10 h-10" />} title="No alerts found" /> : (
              <div className="table-wrapper">
                <table>
                  <thead><tr>
                    <th>Severity</th><th>Title</th><th>Source</th><th>Status</th><th>Created</th><th>Actions</th>
                  </tr></thead>
                  <tbody>
                    {data?.items.map((a) => (
                      <tr key={a.id}>
                        <td><SeverityBadge severity={a.severity} /></td>
                        <td>
                          <div className="font-medium text-gray-200 text-sm">{a.title}</div>
                          <div className="text-xs text-gray-600 mt-0.5 max-w-xs truncate">{a.description}</div>
                        </td>
                        <td className="text-gray-500 text-xs">{a.source}</td>
                        <td><StatusBadge status={a.status} /></td>
                        <td className="text-gray-600 text-xs">{new Date(a.created_at).toLocaleDateString()}</td>
                        <td>
                          <div className="flex gap-2">
                            {a.status === 'open' && (
                              <button onClick={() => acknowledge(a.id)} className="text-xs text-purple-400 hover:text-purple-300 transition-colors">Ack</button>
                            )}
                            {a.status !== 'closed' && (
                              <button onClick={() => close(a.id)} className="text-xs text-gray-500 hover:text-gray-300 transition-colors">Close</button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
          <div className="px-4 pb-4">
            <Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} />
          </div>
        </div>
      </div>
    </Layout>
  );
}
