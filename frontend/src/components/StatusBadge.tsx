interface StatusBadgeProps {
  label: string;
  tone?: 'green' | 'purple' | 'cyan' | 'red' | 'amber' | 'slate';
}

const toneClasses: Record<string, string> = {
  green: 'theme-badge-green',
  purple: 'theme-badge-purple',
  cyan: 'theme-badge-cyan',
  red: 'theme-badge-red',
  amber: 'theme-badge-amber',
  slate: 'theme-badge-slate',
};

export function StatusBadge({ label, tone = 'slate' }: StatusBadgeProps) {
  return <span className={`theme-badge-base ${toneClasses[tone] ?? toneClasses.slate}`}>{label}</span>;
}
