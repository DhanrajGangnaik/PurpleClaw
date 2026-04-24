import { useLocation } from 'react-router-dom';
import { EnvironmentSwitcher } from './EnvironmentSwitcher';
import { ThemeSwitcher } from './ThemeSwitcher';
import { StatusBadge } from './StatusBadge';
import { useAuth } from '../contexts/AuthContext';
import type { ManagedEnvironment } from '../types/api';

const pageTitles: Record<string, { title: string; description: string }> = {
  '/home': {
    title: 'Workspace Home',
    description: 'Overview and entry point for core security workflows.',
  },
  '/': {
    title: 'Workspace Home',
    description: 'Overview and entry point for core security workflows.',
  },
  '/dashboards': {
    title: 'Dashboards',
    description: 'Operational views with high-signal widgets and clear grouping.',
  },
  '/datasources': {
    title: 'Data Sources',
    description: 'Configure connectors and monitor ingestion health.',
  },
  '/scans': {
    title: 'Scans',
    description: 'Run controlled assessments and review output for the active environment.',
  },
  '/reports': {
    title: 'Reports',
    description: 'Generate and download stakeholder-ready assessment reports.',
  },
  '/alerts': {
    title: 'Alerts',
    description: 'Active SOC and NOC alerts for the selected environment.',
  },
  '/settings': {
    title: 'Settings',
    description: 'Manage environments and workspace configuration.',
  },
  '/signals': {
    title: 'Security Signals',
    description: 'Correlation-ready detection signals for the active environment.',
  },
  '/service-health': {
    title: 'Service Health',
    description: 'NOC service health and dependency status.',
  },
  '/dependencies': {
    title: 'Dependencies',
    description: 'External dependency status and health indicators.',
  },
  '/scheduler': {
    title: 'Scheduler',
    description: 'Platform health, backups, and automation job scheduling.',
  },
  '/automation': {
    title: 'Automation',
    description: 'Safe tracking cycles, posture refresh, and telemetry sync.',
  },
  '/plans': {
    title: 'Exercise Plans',
    description: 'Persisted purple-team exercise plans for the environment.',
  },
  '/executions': {
    title: 'Executions',
    description: 'Stub execution results from validated exercise plans.',
  },
  '/validator': {
    title: 'Plan Validator',
    description: 'Validate and safely execute exercise plans.',
  },
  '/policies': {
    title: 'Policies',
    description: 'Defensive control policies and coverage metrics.',
  },
  '/remediation': {
    title: 'Remediation',
    description: 'Remediation tasks mapped to open findings.',
  },
  '/users': {
    title: 'User Management',
    description: 'Manage operator accounts and role-based access control.',
  },
};

interface HeaderProps {
  apiStatus: string;
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onManageEnvironmentRequest: () => void;
  onSidebarToggle: () => void;
}

function HamburgerIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

export function Header({
  apiStatus,
  environments,
  selectedEnvironmentId,
  onEnvironmentChange,
  onManageEnvironmentRequest,
  onSidebarToggle,
}: HeaderProps) {
  const location = useLocation();
  const copy = pageTitles[location.pathname] ?? pageTitles['/'];
  const selectedEnvironment = environments.find((e) => e.environment_id === selectedEnvironmentId) ?? environments[0] ?? null;
  const { user, logout } = useAuth();
  const initials = user ? user.username.slice(0, 2).toUpperCase() : 'PC';

  return (
    <header
      className="sticky top-0 z-10 border-b backdrop-blur-xl"
      style={{ background: 'var(--bg-header)', borderColor: 'var(--border)' }}
    >
      <div className="flex flex-col gap-4 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-3 min-w-0">
          <button
            type="button"
            onClick={onSidebarToggle}
            className="lg:hidden flex h-10 w-10 items-center justify-center rounded-xl border transition-colors shrink-0"
            style={{ borderColor: 'var(--border)', color: 'var(--text-muted)', background: 'var(--bg-elevated)' }}
            aria-label="Open navigation"
          >
            <HamburgerIcon />
          </button>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="workspace-eyebrow">PurpleClaw Workspace</span>
              <StatusBadge label={selectedEnvironment?.status ?? 'offline'} tone={apiStatus === 'online' ? 'green' : 'red'} />
            </div>
            <h2 className="mt-2 text-xl font-semibold leading-tight tracking-tight truncate" style={{ color: 'var(--text-primary)' }}>
              {copy.title}
            </h2>
            <p className="mt-1 text-sm truncate hidden sm:block" style={{ color: 'var(--text-muted)' }}>
              {copy.description}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-end">
          <EnvironmentSwitcher
            environments={environments}
            selectedEnvironmentId={selectedEnvironmentId}
            onEnvironmentChange={onEnvironmentChange}
            onManageEnvironmentRequest={onManageEnvironmentRequest}
            compact
          />

          <ThemeSwitcher />

          <div
            className="flex items-center gap-2.5 rounded-2xl border px-3 py-2"
            style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)' }}
          >
            <span
              className="h-2 w-2 rounded-full shrink-0"
              style={{ background: apiStatus === 'online' ? 'var(--status-success)' : 'var(--status-critical)' }}
            />
            <span className="text-xs font-semibold uppercase tracking-[0.14em]" style={{ color: 'var(--text-secondary)' }}>
              API {apiStatus === 'online' ? 'Online' : 'Offline'}
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-wider hidden md:inline" style={{ color: 'var(--text-disabled)' }}>
              {selectedEnvironment?.type ?? '—'}
            </span>
          </div>

          <div
            className="flex items-center gap-3 rounded-2xl border px-3 py-2"
            style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)' }}
          >
            <div
              className="h-9 w-9 rounded-xl flex items-center justify-center text-[10px] font-bold text-white shrink-0"
              style={{ background: 'var(--gradient-brand)' }}
            >
              {initials}
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>{user?.username ?? 'Operator'}</p>
              <p className="text-[11px] capitalize" style={{ color: 'var(--text-muted)' }}>{user?.role ?? 'analyst'}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              title="Sign out"
              className="ml-1 rounded-lg p-1.5 transition-colors hover:opacity-70"
              style={{ color: 'var(--text-muted)' }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
