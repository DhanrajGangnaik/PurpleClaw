import { useEffect, useState } from 'react';
import { SectionHeader } from '../components/SectionHeader';
import { StatusBadge } from '../components/StatusBadge';
import { useAuth } from '../contexts/AuthContext';
import { authApi } from '../services/auth';
import type { AuthUser, UserCreateRequest } from '../services/auth';

const ROLE_TONES: Record<AuthUser['role'], 'purple' | 'cyan' | 'green'> = {
  admin: 'purple',
  analyst: 'cyan',
  viewer: 'green',
};

export function UserManagement() {
  const { user: currentUser, token } = useAuth();
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<UserCreateRequest>({ username: '', email: '', password: '', role: 'analyst' });
  const [formError, setFormError] = useState('');

  const load = () => {
    if (!token) return;
    setLoading(true);
    authApi.listUsers(token)
      .then(setUsers)
      .catch(() => setError('Failed to load users'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [token]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setCreating(true);
    setFormError('');
    try {
      await authApi.createUser(token, form);
      setShowCreate(false);
      setForm({ username: '', email: '', password: '', role: 'analyst' });
      load();
    } catch {
      setFormError('Failed to create user. Username may already be taken.');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (u: AuthUser) => {
    if (!token || u.user_id === currentUser?.user_id) return;
    try {
      await authApi.updateUser(token, u.user_id, { is_active: !u.is_active });
      load();
    } catch {
      setError('Failed to update user');
    }
  };

  const handleDelete = async (u: AuthUser) => {
    if (!token || u.user_id === currentUser?.user_id) return;
    if (!window.confirm(`Delete user "${u.username}"? This cannot be undone.`)) return;
    try {
      await authApi.deleteUser(token, u.user_id);
      load();
    } catch {
      setError('Failed to delete user');
    }
  };

  if (currentUser?.role !== 'admin') {
    return (
      <div className="workspace-panel p-6">
        <p className="text-sm" style={{ color: 'var(--text-muted)' }}>User management requires admin role.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="User Management"
        description="Manage operator accounts and role-based access."
        action={
          <button type="button" onClick={() => setShowCreate((v) => !v)} className="theme-button-primary rounded-2xl px-4 py-2 text-sm font-semibold">
            {showCreate ? 'Cancel' : 'New User'}
          </button>
        }
      />

      {error && <p className="rounded-xl px-4 py-2 text-sm" style={{ background: 'var(--status-critical-bg, #fef2f2)', color: 'var(--status-critical)' }}>{error}</p>}

      {showCreate && (
        <div className="workspace-panel p-5">
          <h3 className="mb-4 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>Create User</h3>
          <form onSubmit={(e) => { void handleCreate(e); }} className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Username *</label>
              <input required value={form.username} onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                className="w-full rounded-xl border px-3 py-2 text-sm" style={{ background: 'var(--bg-base)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                className="w-full rounded-xl border px-3 py-2 text-sm" style={{ background: 'var(--bg-base)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Password *</label>
              <input required type="password" value={form.password} onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                className="w-full rounded-xl border px-3 py-2 text-sm" style={{ background: 'var(--bg-base)', borderColor: 'var(--border)', color: 'var(--text-primary)' }} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>Role *</label>
              <select value={form.role} onChange={(e) => setForm((f) => ({ ...f, role: e.target.value as AuthUser['role'] }))}
                className="w-full rounded-xl border px-3 py-2 text-sm" style={{ background: 'var(--bg-base)', borderColor: 'var(--border)', color: 'var(--text-primary)' }}>
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            {formError && <p className="col-span-2 text-xs" style={{ color: 'var(--status-critical)' }}>{formError}</p>}
            <div className="col-span-2 flex justify-end">
              <button type="submit" disabled={creating} className="theme-button-primary rounded-xl px-4 py-2 text-sm font-semibold disabled:opacity-50">
                {creating ? 'Creating…' : 'Create User'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="workspace-panel overflow-hidden">
        {loading ? (
          <p className="p-5 text-sm" style={{ color: 'var(--text-muted)' }}>Loading users…</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b" style={{ borderColor: 'var(--border)' }}>
                {['Username', 'Email', 'Role', 'Status', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.user_id} className="border-b last:border-0" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-4 py-3 font-medium" style={{ color: 'var(--text-primary)' }}>
                    {u.username}
                    {u.user_id === currentUser?.user_id && (
                      <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>you</span>
                    )}
                  </td>
                  <td className="px-4 py-3" style={{ color: 'var(--text-muted)' }}>{u.email || '—'}</td>
                  <td className="px-4 py-3"><StatusBadge label={u.role} tone={ROLE_TONES[u.role]} /></td>
                  <td className="px-4 py-3"><StatusBadge label={u.is_active ? 'active' : 'inactive'} tone={u.is_active ? 'green' : 'red'} /></td>
                  <td className="px-4 py-3">
                    {u.user_id !== currentUser?.user_id && (
                      <div className="flex gap-2">
                        <button type="button" onClick={() => { void handleToggleActive(u); }}
                          className="rounded-lg px-2.5 py-1 text-xs font-medium border transition-colors hover:opacity-80"
                          style={{ borderColor: 'var(--border)', color: 'var(--text-secondary)', background: 'var(--bg-elevated)' }}>
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button type="button" onClick={() => { void handleDelete(u); }}
                          className="rounded-lg px-2.5 py-1 text-xs font-medium border transition-colors hover:opacity-80"
                          style={{ borderColor: 'var(--status-critical)', color: 'var(--status-critical)', background: 'transparent' }}>
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="workspace-panel p-4">
        <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: 'var(--text-secondary)' }}>Role Permissions</p>
        <div className="grid gap-2 text-xs sm:grid-cols-3" style={{ color: 'var(--text-muted)' }}>
          <div><span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Admin</span> — Full access including user management, environment delete, platform backup/restore</div>
          <div><span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Analyst</span> — Read + write scans, reports, findings, dashboards, data sources, automation</div>
          <div><span className="font-semibold" style={{ color: 'var(--text-primary)' }}>Viewer</span> — Read-only access to all data</div>
        </div>
      </div>
    </div>
  );
}
