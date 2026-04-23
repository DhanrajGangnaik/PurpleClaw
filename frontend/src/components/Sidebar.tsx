import { NavLink } from 'react-router-dom';
import { Logo } from './Logo';

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggle: () => void;
  onCloseMobile: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: '/home', label: 'Home', icon: 'H' },
  { path: '/dashboards', label: 'Dashboards', icon: 'D' },
  { path: '/alerts', label: 'Alerts', icon: 'A' },
  { path: '/scans', label: 'Scans', icon: 'S' },
  { path: '/reports', label: 'Reports', icon: 'R' },
  { path: '/datasources', label: 'Data Sources', icon: 'DS' },
  { path: '/settings', label: 'Settings', icon: 'C' },
];

export function Sidebar({ collapsed, mobileOpen, onToggle, onCloseMobile }: SidebarProps) {
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-slate-950/45 transition lg:hidden ${mobileOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'}`}
        onClick={onCloseMobile}
      />

      <aside
        className={`theme-surface-strong fixed inset-y-0 left-0 z-40 flex border-r backdrop-blur-2xl transition-all duration-300 ${
          collapsed ? 'w-24' : 'w-72'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
      >
        <div className="flex w-full flex-col px-4 py-5">
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} gap-3`}>
            <div className={`flex items-center gap-3 ${collapsed ? 'justify-center' : ''}`}>
              <Logo className="h-10 w-10 shrink-0" />
              {!collapsed ? (
                <div>
                  <h1 className="theme-text-primary text-xl font-semibold">PurpleClaw</h1>
                  <p className="theme-brand text-xs uppercase tracking-[0.2em]">Workspace</p>
                </div>
              ) : null}
            </div>
            {!collapsed ? (
              <button
                type="button"
                onClick={onToggle}
                className="theme-button-secondary hidden h-10 w-10 items-center justify-center rounded-2xl lg:inline-flex"
                aria-label="Collapse sidebar"
              >
                <span className="theme-text-primary text-lg leading-none">-</span>
              </button>
            ) : null}
          </div>

          {collapsed ? (
            <button
              type="button"
              onClick={onToggle}
              className="theme-button-secondary mt-6 hidden h-10 w-full items-center justify-center rounded-2xl lg:inline-flex"
              aria-label="Expand sidebar"
            >
              <span className="theme-text-primary text-lg leading-none">+</span>
            </button>
          ) : null}

          <nav className="mt-8 flex-1 space-y-2 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `group flex items-center rounded-2xl border px-3 py-3 text-sm font-medium transition ${
                    collapsed ? 'justify-center' : 'gap-3'
                  } ${
                    isActive
                      ? 'border-sky-400/35 bg-sky-400/10 theme-text-primary'
                      : 'border-transparent theme-text-muted hover:border-sky-400/20 hover:bg-[var(--table-hover)] hover:text-[var(--text-primary)]'
                  }`
                }
                title={item.label}
              >
                <span className="theme-inset grid h-10 min-w-10 place-items-center rounded-2xl border text-[11px] font-bold tracking-[0.08em]">
                  {item.icon}
                </span>
                {!collapsed ? <span>{item.label}</span> : null}
              </NavLink>
            ))}
          </nav>

          <div className={`rounded-3xl border border-sky-400/20 bg-gradient-to-br from-sky-500/12 to-emerald-400/12 p-4 ${collapsed ? 'text-center' : ''}`}>
            <p className="theme-text-primary text-sm font-semibold">{collapsed ? 'PC' : 'Cleaner navigation'}</p>
            {!collapsed ? (
              <p className="theme-text-muted mt-2 text-xs leading-5">The sidebar is reduced to the primary areas and can collapse into icon-only mode.</p>
            ) : null}
          </div>
        </div>
      </aside>
    </>
  );
}
