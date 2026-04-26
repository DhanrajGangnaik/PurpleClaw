import { Loader2 } from 'lucide-react';
import type { ReactNode } from 'react';

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sz = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-10 h-10' }[size];
  return <Loader2 className={`${sz} animate-spin text-purple-500`} />;
}

export function PageLoading() {
  return <div className="flex items-center justify-center py-20"><LoadingSpinner size="lg" /></div>;
}

export function EmptyState({ icon, title, description }: { icon?: ReactNode; title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="mb-4 text-gray-600">{icon}</div>}
      <p className="text-gray-400 font-medium">{title}</p>
      {description && <p className="text-gray-600 text-sm mt-1">{description}</p>}
    </div>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  const s = severity?.toLowerCase();
  const cls = s === 'critical' ? 'badge-critical' : s === 'high' ? 'badge-high' : s === 'medium' ? 'badge-medium' : s === 'low' ? 'badge-low' : 'badge-info';
  return <span className={`badge ${cls}`}>{severity}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const s = status?.toLowerCase();
  const cls = s === 'open' || s === 'active' || s === 'new' ? 'badge-high'
    : s === 'in_progress' || s === 'investigating' ? 'badge-medium'
    : s === 'closed' || s === 'resolved' || s === 'completed' ? 'badge-success'
    : s === 'false_positive' ? 'badge-info'
    : 'badge-info';
  return <span className={`badge ${cls}`}>{status?.replace(/_/g, ' ')}</span>;
}

export function MetricCard({ label, value, sub, color = 'purple' }: { label: string; value: string | number; sub?: string; color?: string }) {
  const accent = color === 'red' ? 'text-red-400' : color === 'orange' ? 'text-orange-400' : color === 'green' ? 'text-green-400' : color === 'blue' ? 'text-blue-400' : 'text-purple-400';
  return (
    <div className="metric-card">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold mt-1 ${accent}`}>{value}</p>
      {sub && <p className="text-xs text-gray-600 mt-0.5">{sub}</p>}
    </div>
  );
}

export function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (p: number) => void }) {
  if (pages <= 1) return null;
  return (
    <div className="flex items-center gap-2 mt-4 justify-end">
      <button onClick={() => onChange(page - 1)} disabled={page <= 1} className="btn-secondary py-1 px-3 disabled:opacity-40">Prev</button>
      <span className="text-sm text-gray-500">Page {page} of {pages}</span>
      <button onClick={() => onChange(page + 1)} disabled={page >= pages} className="btn-secondary py-1 px-3 disabled:opacity-40">Next</button>
    </div>
  );
}

export function SearchBar({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder ?? 'Search...'}
      className="w-64"
    />
  );
}
