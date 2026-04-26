import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getUsers } from '../../services/api';
import type { User, Paginated } from '../../services/api';
import { Users as UsersIcon } from 'lucide-react';

const roleColor = (r: string) => r === 'admin' ? 'badge-critical' : r === 'analyst' ? 'badge-medium' : 'badge-info';

export function UsersPage() {
  const [data, setData] = useState<Paginated<User> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getUsers(page, 25).then(setData).finally(() => setLoading(false));
  }, [page]);

  return (
    <Layout title="User Management">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Users" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Active" value={data?.items.filter((u) => u.is_active).length ?? 0} color="green" />
          <MetricCard label="Admins" value={data?.items.filter((u) => u.role === 'admin').length ?? 0} color="red" />
        </div>
        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <UsersIcon className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">User Accounts</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState title="No users" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Username</th><th>Full Name</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {data?.items.map((u) => (
                    <tr key={u.id}>
                      <td className="font-medium text-gray-200">{u.username}</td>
                      <td className="text-gray-400">{u.full_name}</td>
                      <td className="text-gray-500 text-xs">{u.email}</td>
                      <td><span className={`badge ${roleColor(u.role)}`}>{u.role}</span></td>
                      <td>{u.is_active ? <span className="badge badge-success">Active</span> : <span className="badge badge-info">Inactive</span>}</td>
                      <td className="text-gray-600 text-xs">{new Date(u.created_at).toLocaleDateString()}</td>
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
