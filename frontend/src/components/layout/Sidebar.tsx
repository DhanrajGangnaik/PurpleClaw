import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Shield, AlertTriangle, FlameKindling, Crosshair,
  Bug, FileBarChart2, Settings, ChevronLeft, ChevronRight,
  Radar, Activity, Search, Globe, FolderOpen, Target,
  Network, Eye, Server, BookOpen, CheckSquare, Users,
  Cpu, Swords, FileText, ShieldCheck, ChevronDown, ChevronUp, Zap
} from 'lucide-react';
import { useState } from 'react';

interface SidebarProps { collapsed: boolean; onToggle: () => void; }

const groups = [
  {
    label: 'Operations',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/soc/alerts', icon: AlertTriangle, label: 'Alerts' },
      { to: '/soc/incidents', icon: FlameKindling, label: 'Incidents' },
      { to: '/soc/cases', icon: FolderOpen, label: 'Cases' },
      { to: '/soc/siem', icon: Activity, label: 'SIEM' },
    ],
  },
  {
    label: 'Network & Assets',
    items: [
      { to: '/noc/assets', icon: Server, label: 'Assets' },
      { to: '/noc/network', icon: Network, label: 'Network' },
    ],
  },
  {
    label: 'Red Team',
    items: [
      { to: '/redteam/plans', icon: Target, label: 'Attack Plans' },
      { to: '/redteam/executions', icon: Swords, label: 'Executions' },
      { to: '/redteam/recon', icon: Search, label: 'Recon' },
      { to: '/redteam/payloads', icon: Cpu, label: 'Payloads' },
    ],
  },
  {
    label: 'Blue Team',
    items: [
      { to: '/blueteam/rules', icon: ShieldCheck, label: 'Detection Rules' },
      { to: '/blueteam/hunting', icon: Radar, label: 'Threat Hunting' },
      { to: '/blueteam/edr', icon: Eye, label: 'EDR Events' },
      { to: '/blueteam/fim', icon: FileText, label: 'FIM' },
    ],
  },
  {
    label: 'Purple Team',
    items: [
      { to: '/purpleteam/exercises', icon: BookOpen, label: 'Exercises' },
      { to: '/purpleteam/coverage', icon: CheckSquare, label: 'ATT&CK Coverage' },
    ],
  },
  {
    label: 'Threat Intel',
    items: [
      { to: '/intel/iocs', icon: Crosshair, label: 'IOCs' },
      { to: '/intel/actors', icon: Users, label: 'Threat Actors' },
      { to: '/intel/campaigns', icon: Globe, label: 'Campaigns' },
      { to: '/intel/feeds', icon: Radar, label: 'Feeds' },
    ],
  },
  {
    label: 'Vulnerabilities',
    items: [
      { to: '/vulns/list', icon: Bug, label: 'Vulnerabilities' },
      { to: '/vulns/findings', icon: AlertTriangle, label: 'Findings' },
      { to: '/vulns/scans', icon: Search, label: 'Scans' },
    ],
  },
  {
    label: 'Incident Response',
    items: [
      { to: '/ir/playbooks', icon: BookOpen, label: 'Playbooks' },
      { to: '/ir/executions', icon: Activity, label: 'IR Executions' },
    ],
  },
  {
    label: 'Compliance',
    items: [
      { to: '/compliance/frameworks', icon: CheckSquare, label: 'Frameworks' },
    ],
  },
  {
    label: 'Platform',
    items: [
      { to: '/reports', icon: FileBarChart2, label: 'Reports' },
      { to: '/settings/users', icon: Users, label: 'Users' },
      { to: '/settings/audit', icon: Shield, label: 'Audit Log' },
      { to: '/settings/system', icon: Settings, label: 'System' },
      { to: '/settings/engine', icon: Zap, label: 'Engine Status' },
    ],
  },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(groups.map((g) => [g.label, true]))
  );
  const toggle = (label: string) => setOpenGroups((s) => ({ ...s, [label]: !s[label] }));

  return (
    <div className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-gray-950 border-r border-gray-800/80 transition-all duration-300 ${collapsed ? 'w-16' : 'w-60'}`}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-800/80">
        <div className="w-7 h-7 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
          <Shield className="w-4 h-4 text-white" />
        </div>
        {!collapsed && <span className="text-sm font-bold text-white tracking-wide">PurpleClaw</span>}
        <button onClick={onToggle} className="ml-auto text-gray-600 hover:text-gray-400 transition-colors flex-shrink-0">
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {groups.map((group) => (
          <div key={group.label}>
            {!collapsed && (
              <button
                onClick={() => toggle(group.label)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-gray-600 uppercase tracking-wider hover:text-gray-400 transition-colors"
              >
                {group.label}
                {openGroups[group.label] ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>
            )}
            {(collapsed || openGroups[group.label]) && group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''} ${collapsed ? 'justify-center' : ''}`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </div>
  );
}
