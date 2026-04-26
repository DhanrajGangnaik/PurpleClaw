import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, Pagination, EmptyState } from '../../components/ui';
import { getAuditLogs } from '../../services/api';
import type { AuditLog, Paginated } from '../../services/api';
import { Shield } from 'lucide-react';

export function AuditLog() {
  const [data, setData] = useState<Paginated<AuditLog> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAuditLogs(page, 50).then(setData).finally(() => setLoading(false));
  }, [page]);

  const actionColor = (a: string) => a.startsWith('create') ? 'text-green-400' : a.startsWith('delete') ? 'text-red-400' : a.startsWith('update') ? 'text-yellow-400' : 'text-blue-400';

  return (
    <Layout title="Audit Log">
      <div className="card">
        <div className="p-4 border-b border-gray-800 flex items-center gap-2">
          <Shield className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-gray-300">Audit Trail</h2>
          <span className="badge badge-purple ml-auto">{data?.total ?? 0} records</span>
        </div>
        {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No audit records" /> : (
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Action</th><th>Resource</th><th>Resource ID</th><th>User</th><th>IP</th><th>Timestamp</th></tr></thead>
              <tbody>
                {data?.items.map((log) => (
                  <tr key={log.id}>
                    <td className={`font-mono text-xs font-semibold ${actionColor(log.action)}`}>{log.action}</td>
                    <td className="text-gray-400 text-xs">{log.resource_type}</td>
                    <td className="text-gray-600 font-mono text-xs">{log.resource_id}</td>
                    <td className="text-gray-500 text-xs">User #{log.user_id}</td>
                    <td className="text-gray-600 font-mono text-xs">{log.ip_address}</td>
                    <td className="text-gray-600 text-xs">{new Date(log.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="px-4 pb-4"><Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} /></div>
      </div>
    </Layout>
  );
}
