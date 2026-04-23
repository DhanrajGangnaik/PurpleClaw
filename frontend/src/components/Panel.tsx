import type { ReactNode } from 'react';
import { Card } from './Card';
import { SectionHeader } from './SectionHeader';

interface PanelProps {
  title: string;
  eyebrow?: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}

export function Panel({ title, eyebrow, description, children, action, className = '' }: PanelProps) {
  return (
    <Card className={`p-5 ${className}`}>
      <SectionHeader title={title} eyebrow={eyebrow} description={description} action={action} />
      {children}
    </Card>
  );
}
