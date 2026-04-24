import type { ReactElement } from 'react';

interface MetricCardProps {
  title: string;
  value: string | number;
  caption: string;
  accent?: 'cyan' | 'purple' | 'pink' | 'green' | 'amber';
  icon?: ReactElement;
}

const accentStyles: Record<string, { dot: string; text: string }> = {
  cyan: { dot: '#008FEC', text: '#008FEC' },
  purple: { dot: '#9013FE', text: '#9013FE' },
  pink: { dot: '#FC4D64', text: '#FC4D64' },
  green: { dot: '#3EBD41', text: '#3EBD41' },
  amber: { dot: '#F3AD38', text: '#F3AD38' },
};

export function MetricCard({ title, value, caption, accent = 'cyan', icon }: MetricCardProps) {
  const style = accentStyles[accent] ?? accentStyles.cyan;

  return (
    <section className="kpi-card flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em]" style={{ color: 'var(--text-muted)' }}>
            {title}
          </p>
          <p className="mt-3 text-3xl font-semibold leading-none tracking-tight" style={{ color: 'var(--text-primary)' }}>
            {value}
          </p>
        </div>
        <div
          className="flex h-10 w-10 items-center justify-center rounded-xl border"
          style={{ borderColor: 'var(--border)', background: 'var(--surface-overlay)', color: style.text }}
        >
          {icon ?? <span className="h-2.5 w-2.5 rounded-full" style={{ background: style.dot }} />}
        </div>
      </div>
      <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
        <span className="h-1.5 w-1.5 rounded-full" style={{ background: style.dot }} />
        <span className="leading-relaxed">{caption}</span>
      </div>
    </section>
  );
}
