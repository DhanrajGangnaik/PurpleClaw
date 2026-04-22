interface StatusBadgeProps {
  label: string;
  tone?: 'green' | 'purple' | 'cyan' | 'red' | 'slate';
}

const tones = {
  green: 'theme-badge-green',
  purple: 'theme-badge-purple',
  cyan: 'theme-badge-cyan',
  red: 'theme-badge-red',
  slate: 'theme-badge-slate',
};

export function StatusBadge({ label, tone = 'slate' }: StatusBadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${tones[tone]}`}>
      {label}
    </span>
  );
}
