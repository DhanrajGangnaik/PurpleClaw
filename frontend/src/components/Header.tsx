import { useLocation } from 'react-router-dom';
import { ThemeSwitcher } from './ThemeSwitcher';
import type { ManagedEnvironment } from '../types/api';

const pageTitles: Record<string, { title: string; description: string }> = {
  '/': {
    title: 'Security Operations Overview',
    description: 'Posture, findings, remediation, telemetry, and tracking status in one SOC workspace.',
  },
  '/plans': {
    title: 'Validation Plans',
    description: 'Review approved validation plans and expected defensive telemetry.',
  },
  '/executions': {
    title: 'Validation Results',
    description: 'Inspect safe validation outcomes and posture verification records.',
  },
  '/assets': {
    title: 'Assets',
    description: 'Review asset exposure, ownership, and posture signals.',
  },
  '/findings': {
    title: 'Findings',
    description: 'Prioritize defensive findings and verification evidence.',
  },
  '/remediation': {
    title: 'Remediation',
    description: 'Track remediation tasks and verification progress.',
  },
  '/policies': {
    title: 'Policies',
    description: 'Review defensive posture policies and control coverage.',
  },
  '/reports': {
    title: 'Reports',
    description: 'Inspect generated posture and telemetry reports.',
  },
  '/automation': {
    title: 'Automation',
    description: 'Run safe tracking cycles and review automation history.',
  },
  '/validator': {
    title: 'Plan Validator',
    description: 'Validate posture plans before recording safe verification results.',
  },
};

interface HeaderProps {
  apiStatus: string;
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
}

export function Header({ apiStatus, environments, selectedEnvironmentId, onEnvironmentChange }: HeaderProps) {
  const location = useLocation();
  const copy = pageTitles[location.pathname] ?? pageTitles['/'];
  const selectedEnvironment = environments.find((environment) => environment.environment_id === selectedEnvironmentId);

  return (
    <header className="theme-surface-strong sticky top-0 z-10 border-b px-4 py-4 backdrop-blur-2xl sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="max-w-3xl">
          <p className="theme-brand text-xs font-semibold uppercase tracking-[0.2em]">PurpleClaw</p>
          <h2 className="theme-text-primary mt-1 text-2xl font-semibold">{copy.title}</h2>
          <p className="theme-text-muted mt-1 text-sm">{copy.description}</p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-end">
          <label className="theme-inset flex h-10 items-center gap-2 rounded-2xl border px-3">
            <span className="theme-text-faint text-xs font-semibold uppercase tracking-[0.14em]">Env</span>
            <select
              value={selectedEnvironmentId}
              onChange={(event) => onEnvironmentChange(event.target.value)}
              className="theme-text-primary min-w-32 bg-transparent text-sm font-semibold outline-none"
              aria-label="Select environment"
            >
              {environments.length ? (
                environments.map((environment) => (
                  <option key={environment.environment_id} value={environment.environment_id}>
                    {environment.name}
                  </option>
                ))
              ) : (
                <option value={selectedEnvironmentId}>Homelab</option>
              )}
            </select>
          </label>
          <ThemeSwitcher />
          <label className="relative block">
            <span className="sr-only">Search dashboard</span>
            <span className="theme-text-faint pointer-events-none absolute left-3 top-2.5 text-sm">/</span>
            <input
              className="theme-input theme-focus h-10 w-full rounded-2xl border pl-9 pr-4 text-sm transition sm:w-72"
              placeholder="Search posture data..."
              type="search"
            />
          </label>
          <div className="theme-inset flex items-center gap-3 rounded-2xl border px-3 py-2">
            <span className={`h-2.5 w-2.5 rounded-full ${apiStatus === 'online' ? 'bg-signal' : 'bg-rose-400'}`} />
            <span className="theme-text-secondary text-sm">API {apiStatus}</span>
            <span className="theme-text-faint hidden text-xs uppercase tracking-[0.12em] sm:inline">{selectedEnvironment?.type ?? 'homelab'}</span>
            <div className="grid h-8 w-8 place-items-center rounded-xl bg-gradient-to-br from-fuchsia-500 to-cyan-400 text-xs font-bold !text-white">
              SOC
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
