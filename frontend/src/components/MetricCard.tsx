interface MetricCardProps {
  title: string;
  value: string | number;
  caption: string;
  accent?: 'cyan' | 'purple' | 'pink' | 'green';
}

const accents = {
  cyan: 'theme-badge-cyan',
  purple: 'theme-badge-purple',
  pink: 'theme-badge-red',
  green: 'theme-badge-green',
};

export function MetricCard({ title, value, caption, accent = 'purple' }: MetricCardProps) {
  return (
    <section className="theme-surface min-h-36 rounded-card border p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="theme-text-muted text-sm font-medium">{title}</p>
          <p className="theme-text-primary mt-3 text-3xl font-semibold tracking-tight">{value}</p>
          <p className="theme-text-faint mt-2 text-sm">{caption}</p>
        </div>
        <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${accents[accent]}`}>{title}</span>
      </div>
    </section>
  );
}
