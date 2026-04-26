import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getScanJobs, createScanJob } from '../../services/api';
import type { ScanJob, Paginated } from '../../services/api';
import { Search, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

export function Scans() {
  const [data, setData] = useState<Paginated<ScanJob> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); getScanJobs(page, 25).then(setData).finally(() => setLoading(false)); };
  useEffect(() => { load(); }, [page]);

  const runScan = async () => {
    try {
      await createScanJob({ name: `Manual Scan ${new Date().toLocaleTimeString()}`, scan_type: 'vulnerability', status: 'running', target_assets: [] });
      toast.success('Scan started');
      load();
    } catch { toast.error('Failed to start scan'); }
  };

  return (
    <Layout title="Scans">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Scans" value={data?.total ?? 0} color="blue" />
          <MetricCard label="Running" value={data?.items.filter((s) => s.status === 'running').length ?? 0} color="orange" />
          <MetricCard label="Completed" value={data?.items.filter((s) => s.status === 'completed').length ?? 0} color="green" />
          <MetricCard label="Total Findings" value={data?.items.reduce((s, j) => s + j.findings_count, 0) ?? 0} color="red" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Search className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Scan History</h2>
            <button onClick={runScan} className="btn-primary ml-auto flex items-center gap-1">
              <Plus className="w-4 h-4" /> Run Scan
            </button>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No scans" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Name</th><th>Type</th><th>Status</th><th>Findings</th><th>Started</th><th>Completed</th></tr></thead>
                <tbody>
                  {data?.items.map((s) => (
                    <tr key={s.id}>
                      <td className="font-medium text-gray-200">{s.name}</td>
                      <td><span className="badge badge-blue">{s.scan_type}</span></td>
                      <td><StatusBadge status={s.status} /></td>
                      <td className="text-gray-400 text-sm">{s.findings_count}</td>
                      <td className="text-gray-600 text-xs">{s.started_at ? new Date(s.started_at).toLocaleString() : '-'}</td>
                      <td className="text-gray-600 text-xs">{s.completed_at ? new Date(s.completed_at).toLocaleString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="px-4 pb-4"><Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} /></div>
        </div>
      </div>
    </Layout>
  );
}
