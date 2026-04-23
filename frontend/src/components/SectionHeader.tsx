import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  eyebrow?: string;
  description?: string;
  action?: ReactNode;
}

export function SectionHeader({ title, eyebrow, description, action }: SectionHeaderProps) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div>
        {eyebrow && <p className="theme-text-faint text-[11px] font-semibold uppercase tracking-[0.18em]">{eyebrow}</p>}
        <h2 className="theme-text-primary mt-1 text-lg font-semibold">{title}</h2>
        {description && <p className="theme-text-muted mt-2 max-w-2xl text-sm leading-6">{description}</p>}
      </div>
      {action}
    </div>
  );
}
