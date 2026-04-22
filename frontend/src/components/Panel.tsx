import type { ReactNode } from 'react';

interface PanelProps {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Panel({ title, eyebrow, children, action, className = '' }: PanelProps) {
  return (
    <section className={`theme-surface rounded-2xl border p-5 backdrop-blur-xl ${className}`}>
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          {eyebrow && <p className="theme-brand text-[11px] font-bold uppercase tracking-[0.22em]">{eyebrow}</p>}
          <h2 className="theme-text-primary mt-1 text-lg font-semibold">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
