import type { ReactNode } from 'react';
import { Card } from '../Card';
import { SectionHeader } from '../SectionHeader';
import { StatusBadge } from '../StatusBadge';
import { formatDate } from '../../utils';

interface WidgetCardProps {
  title: string;
  type: string;
  freshness?: 'fresh' | 'stale';
  lastUpdated?: string | null;
  children: ReactNode;
}

export function WidgetCard({ title, type, freshness, lastUpdated, children }: WidgetCardProps) {
  const tone = freshness === 'fresh' ? 'green' : freshness === 'stale' ? 'red' : 'slate';

  return (
    <Card className="p-5 sm:p-6">
      <SectionHeader
        title={title}
        eyebrow={type.replace(/_/g, ' ')}
        action={
          <div className="flex flex-wrap items-center gap-2">
            {freshness ? <StatusBadge label={freshness} tone={tone} /> : null}
            {lastUpdated ? <span className="theme-text-faint text-xs">Updated {formatDate(lastUpdated)}</span> : null}
          </div>
        }
      />
      {children}
    </Card>
  );
}
