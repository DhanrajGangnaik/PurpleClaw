import type { ReactNode } from 'react';

interface SectionHeaderProps {
  title: string;
  eyebrow?: string;
  description?: string;
  action?: ReactNode;
}

export function SectionHeader({ title, eyebrow, description, action }: SectionHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        {eyebrow ? <p className="workspace-eyebrow mb-2">{eyebrow}</p> : null}
        <h2 className="text-lg font-semibold tracking-tight" style={{ color: 'var(--text-primary)' }}>{title}</h2>
        {description ? (
          <p className="mt-2 max-w-3xl text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
