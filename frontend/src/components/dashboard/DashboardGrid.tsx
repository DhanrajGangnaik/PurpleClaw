import type { ReactNode } from 'react';

interface DashboardGridProps {
  children: ReactNode;
  variant?: 'kpi' | 'primary' | 'secondary';
}

const variants = {
  kpi: 'grid gap-4 md:grid-cols-2 xl:grid-cols-4',
  primary: 'grid gap-4 xl:grid-cols-[1.4fr,1fr]',
  secondary: 'grid gap-4 xl:grid-cols-2 2xl:grid-cols-3',
};

export function DashboardGrid({ children, variant = 'secondary' }: DashboardGridProps) {
  return <div className={variants[variant]}>{children}</div>;
}
