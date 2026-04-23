import { useLocation } from 'react-router-dom';
import { EnvironmentSwitcher } from './EnvironmentSwitcher';
import { ThemeSwitcher } from './ThemeSwitcher';
import type { ManagedEnvironment } from '../types/api';

const pageTitles: Record<string, { title: string; description: string }> = {
  '/home': {
    title: 'Workspace Home',
    description: 'Use the homepage as the main entry point for switching environments and jumping into core workflows.',
  },
  '/': {
    title: 'Workspace Home',
    description: 'Use the homepage as the main entry point for switching environments and jumping into core workflows.',
  },
  '/dashboards': {
    title: 'Dashboards',
    description: 'Focused dashboards with fewer, higher-signal widgets and clearer grouping.',
  },
  '/datasources': {
    title: 'Data Sources',
    description: 'Configure ingestion and connector health without leaving the main workflow.',
  },
  '/scans': {
    title: 'Scans',
    description: 'Run controlled assessments and review the most relevant scan output.',
  },
  '/reports': {
    title: 'Reports',
    description: 'Generate concise reports and keep stakeholder output close to operations.',
  },
  '/alerts': {
    title: 'Alerts',
    description: 'Review active SOC and NOC alerts for the currently selected environment.',
  },
  '/settings': {
    title: 'Settings',
    description: 'Manage environments and tune the application shell.',
  },
};

interface HeaderProps {
  apiStatus: string;
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onCreateEnvironmentRequest: () => void;
  onManageEnvironmentRequest: () => void;
  onSidebarToggle: () => void;
}

export function Header({
  apiStatus,
  environments,
  selectedEnvironmentId,
  onEnvironmentChange,
  onCreateEnvironmentRequest,
  onManageEnvironmentRequest,
  onSidebarToggle,
}: HeaderProps) {
  const location = useLocation();
  const copy = pageTitles[location.pathname] ?? pageTitles['/'];
  const selectedEnvironment = environments.find((environment) => environment.environment_id === selectedEnvironmentId) ?? environments[0];

  return (
    <header className="theme-surface-strong sticky top-0 z-10 border-b px-4 py-4 backdrop-blur-2xl sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="max-w-3xl">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onSidebarToggle}
              className="theme-button-secondary inline-flex h-10 w-10 items-center justify-center rounded-2xl lg:hidden"
              aria-label="Open navigation"
            >
              <span className="space-y-1">
                <span className="block h-0.5 w-4 bg-current" />
                <span className="block h-0.5 w-4 bg-current" />
                <span className="block h-0.5 w-4 bg-current" />
              </span>
            </button>
            <p className="theme-brand text-xs font-semibold uppercase tracking-[0.2em]">PurpleClaw</p>
          </div>
          <h2 className="theme-text-primary mt-1 text-2xl font-semibold">{copy.title}</h2>
          <p className="theme-text-muted mt-1 text-sm">{copy.description}</p>
        </div>

        <div className="flex flex-col gap-3 xl:items-end">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
            <EnvironmentSwitcher
              environments={environments}
              selectedEnvironmentId={selectedEnvironmentId}
              onEnvironmentChange={onEnvironmentChange}
              onCreateEnvironmentRequest={onCreateEnvironmentRequest}
              onManageEnvironmentRequest={onManageEnvironmentRequest}
              compact
            />
            <ThemeSwitcher />
          </div>

          <div className="theme-inset flex items-center gap-3 self-start rounded-2xl border px-3 py-2 xl:self-end">
            <span className={`h-2.5 w-2.5 rounded-full ${apiStatus === 'online' ? 'bg-signal' : 'bg-rose-400'}`} />
            <span className="theme-text-secondary text-sm">API {apiStatus}</span>
            <span className="theme-text-faint hidden text-xs uppercase tracking-[0.12em] sm:inline">{selectedEnvironment?.type ?? 'lab'}</span>
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-sky-500 to-emerald-400 text-xs font-bold text-slate-950">
              PC
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
