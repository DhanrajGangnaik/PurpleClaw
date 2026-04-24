import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
  const { login, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
    } catch {
      setError('Invalid username or password.');
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4" style={{ background: 'var(--bg-base)' }}>
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl text-white font-bold text-lg"
            style={{ background: 'var(--gradient-brand)' }}
          >
            PC
          </div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            PurpleClaw
          </h1>
          <p className="mt-1 text-sm" style={{ color: 'var(--text-muted)' }}>
            Sign in to your workspace
          </p>
        </div>

        <div
          className="rounded-2xl border p-6"
          style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border)' }}
        >
          <form onSubmit={(e) => { void handleSubmit(e); }} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                Username
              </label>
              <input
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2"
                style={{
                  background: 'var(--bg-base)',
                  borderColor: 'var(--border)',
                  color: 'var(--text-primary)',
                }}
                placeholder="admin"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text-secondary)' }}>
                Password
              </label>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border px-3 py-2.5 text-sm outline-none transition-colors focus:ring-2"
                style={{
                  background: 'var(--bg-base)',
                  borderColor: 'var(--border)',
                  color: 'var(--text-primary)',
                }}
                placeholder="••••••••"
              />
            </div>

            {error && (
              <p className="rounded-lg px-3 py-2 text-xs" style={{ background: 'var(--status-critical-bg, #fef2f2)', color: 'var(--status-critical)' }}>
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="theme-button-primary w-full rounded-xl py-2.5 text-sm font-semibold disabled:opacity-50"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <p className="mt-4 text-center text-[11px]" style={{ color: 'var(--text-disabled)' }}>
            Default: <span className="font-mono">admin</span> / <span className="font-mono">purpleclaw-admin</span>
          </p>
        </div>
      </div>
    </div>
  );
}
