import type { ReactElement } from 'react';
import { NavLink } from 'react-router-dom';
import { Logo } from './Logo';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggle: () => void;
  onCloseMobile: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: ReactElement;
}

function IconHome() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9,22 9,12 15,12 15,22" />
    </svg>
  );
}

function IconDashboard() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  );
}

function IconAlerts() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function IconScans() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

function IconReports() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14,2 14,8 20,8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10,9 9,9 8,9" />
    </svg>
  );
}

function IconDataSources() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
    </svg>
  );
}

function IconSettings() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}

function IconChevronLeft() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function IconChevronRight() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function IconUsers() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87" />
      <path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  );
}

const coreNavItems: NavItem[] = [
  { path: '/home', label: 'Home', icon: <IconHome /> },
  { path: '/dashboards', label: 'Dashboards', icon: <IconDashboard /> },
  { path: '/alerts', label: 'Alerts', icon: <IconAlerts /> },
  { path: '/scans', label: 'Scans', icon: <IconScans /> },
  { path: '/reports', label: 'Reports', icon: <IconReports /> },
  { path: '/datasources', label: 'Data Sources', icon: <IconDataSources /> },
];

const adminNavItems: NavItem[] = [
  { path: '/users', label: 'Users', icon: <IconUsers /> },
  { path: '/settings', label: 'Settings', icon: <IconSettings /> },
];

export function Sidebar({ collapsed, mobileOpen, onToggle, onCloseMobile }: SidebarProps) {
  const { user } = useAuth();
  const navItems = [...coreNavItems, ...(user?.role === 'admin' ? adminNavItems : [{ path: '/settings', label: 'Settings', icon: <IconSettings /> }])];
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-black/50 backdrop-blur-sm transition-all duration-200 lg:hidden ${
          mobileOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'
        }`}
        onClick={onCloseMobile}
      />

      <aside
        style={{ background: 'var(--bg-sidebar)', borderColor: 'var(--border)' }}
        className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r transition-all duration-300 ${
          collapsed ? 'w-[72px]' : 'w-72'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}
      >
        <div className={`flex h-20 shrink-0 items-center border-b px-4 ${collapsed ? 'justify-center' : 'gap-3 justify-between'}`} style={{ borderColor: 'var(--border)' }}>
          <div className={`flex items-center gap-3 min-w-0 ${collapsed ? 'justify-center' : ''}`}>
            <div className="shrink-0">
              <Logo className="h-8 w-8" />
            </div>
            {!collapsed ? (
              <div className="min-w-0">
                <p className="text-sm font-bold tracking-tight" style={{ color: 'var(--text-primary)' }}>PurpleClaw</p>
                <p className="text-[10px] font-semibold uppercase tracking-[0.2em]" style={{ color: 'var(--text-muted)' }}>
                  Security Operations
                </p>
              </div>
            ) : null}
          </div>

          {!collapsed ? (
            <button
              type="button"
              onClick={onToggle}
              title="Collapse sidebar"
              className="hidden lg:flex h-7 w-7 items-center justify-center rounded-lg transition-colors shrink-0"
              style={{ color: 'var(--text-muted)' }}
            >
              <IconChevronLeft />
            </button>
          ) : null}
        </div>

        {collapsed ? (
          <button
            type="button"
            onClick={onToggle}
            title="Expand sidebar"
            className="hidden lg:flex mx-3 mt-3 h-8 items-center justify-center rounded-lg border transition-colors shrink-0"
            style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}
          >
            <IconChevronRight />
          </button>
        ) : (
          <div className="px-4 pt-4">
            <div className="rounded-2xl border p-3" style={{ borderColor: 'var(--border)', background: 'var(--surface-overlay)' }}>
              <p className="workspace-eyebrow">Workspace Mode</p>
              <p className="mt-2 text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>SOC / NOC Command Center</p>
              <p className="mt-1 text-xs leading-5" style={{ color: 'var(--text-muted)' }}>
                High-signal navigation for monitoring, scanning, reporting, and connector management.
              </p>
            </div>
          </div>
        )}

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onCloseMobile}
              title={item.label}
              className={({ isActive }) =>
                `theme-sidebar-item group flex items-center rounded-2xl transition-all duration-150 ${
                  collapsed ? 'justify-center px-2 py-2.5' : 'gap-3 px-3 py-2.5'
                } ${isActive ? 'theme-sidebar-item-active' : ''}`
              }
              style={({ isActive }) => ({
                color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
              })}
            >
              <span className="shrink-0 relative z-[1]">{item.icon}</span>
              {!collapsed ? <span className="text-sm font-medium relative z-[1]">{item.label}</span> : null}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t shrink-0" style={{ borderColor: 'var(--border)' }}>
          {collapsed ? (
            <div className="flex justify-center">
              <div className="h-9 w-9 rounded-xl flex items-center justify-center text-xs font-bold text-white" style={{ background: 'var(--gradient-brand)' }}>
                PC
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border p-3" style={{ background: 'var(--bg-elevated)', borderColor: 'var(--border)' }}>
              <p className="text-xs font-semibold" style={{ color: 'var(--text-primary)' }}>Workspace Status</p>
              <p className="mt-1 text-[11px]" style={{ color: 'var(--text-muted)' }}>
                Enterprise shell active with restrained alerting accents and dense operational navigation.
              </p>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
