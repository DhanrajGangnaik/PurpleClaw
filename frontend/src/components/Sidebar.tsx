import { NavLink } from 'react-router-dom';
import { Logo } from './Logo';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Overview', icon: 'O' },
  { path: '/assets', label: 'Assets', icon: 'A' },
  { path: '/inventory', label: 'Inventory', icon: 'I' },
  { path: '/findings', label: 'Findings', icon: 'F' },
  { path: '/remediation', label: 'Remediation', icon: 'R' },
  { path: '/alerts', label: 'Alerts', icon: 'L' },
  { path: '/signals', label: 'Security Signals', icon: 'S' },
  { path: '/service-health', label: 'Service Health', icon: 'H' },
  { path: '/dependencies', label: 'Dependencies', icon: 'D' },
  { path: '/scheduler', label: 'Operations', icon: 'O' },
  { path: '/automation', label: 'Automation', icon: 'A' },
  { path: '/policies', label: 'Policies', icon: 'P' },
  { path: '/reports', label: 'Reports', icon: 'R' },
  { path: '/validator', label: 'Validator', icon: 'V' },
  { path: '/plans', label: 'Plans', icon: 'P' },
  { path: '/executions', label: 'Executions', icon: 'E' },
];

export function Sidebar() {
  return (
    <aside className="theme-surface-strong fixed inset-y-0 left-0 z-20 hidden w-72 border-r px-5 py-6 backdrop-blur-2xl lg:block">
      <div className="flex items-center gap-3">
        <div className="flex items-center">
          <Logo className="h-10 w-10" />
        </div>
        <div>
          <h1 className="theme-text-primary text-xl font-semibold">PurpleClaw</h1>
          <p className="theme-brand text-xs uppercase tracking-[0.2em]">SOC Validation</p>
        </div>
      </div>

      <nav className="mt-8 max-h-[calc(100vh-15rem)] space-y-2 overflow-y-auto pr-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `group flex w-full items-center gap-3 rounded-2xl border px-4 py-3 text-left text-sm font-medium transition duration-200 ${
                isActive
                  ? 'border-fuchsia-400/40 bg-fuchsia-400/10 text-[var(--text-primary)] shadow-[0_0_34px_rgba(217,70,239,0.13)]'
                  : 'border-transparent theme-text-muted hover:border-fuchsia-400/20 hover:bg-fuchsia-400/10 hover:text-[var(--text-primary)]'
              }`
            }
          >
            {({ isActive }) => (
              <>
              <span
                className={`grid h-8 w-8 place-items-center rounded-xl text-xs font-bold ${
                  isActive ? 'bg-gradient-to-br from-fuchsia-400 to-cyan-300 text-slate-950' : 'theme-inset theme-text-secondary'
                }`}
              >
                {item.icon}
              </span>
              {item.label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="absolute bottom-6 left-5 right-5 rounded-2xl border border-fuchsia-400/20 bg-gradient-to-br from-fuchsia-500/10 to-cyan-400/10 p-4">
        <p className="theme-brand text-sm font-semibold">Safe validation</p>
        <p className="theme-text-muted mt-2 text-xs leading-5">
          PurpleClaw records defensive verification without running offensive actions.
        </p>
      </div>
    </aside>
  );
}
