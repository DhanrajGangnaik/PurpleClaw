interface MetricCardProps {
  title: string;
  value: string | number;
  caption: string;
  accent?: 'cyan' | 'purple' | 'pink' | 'green';
}

const accents = {
  cyan: 'from-cyan-400 to-blue-500 text-cyan-200',
  purple: 'from-violet-500 to-purple-400 text-violet-200',
  pink: 'from-fuchsia-500 to-pink-400 text-fuchsia-200',
  green: 'from-emerald-400 to-teal-400 text-emerald-200',
};

export function MetricCard({ title, value, caption, accent = 'purple' }: MetricCardProps) {
  return (
    <section className="theme-surface group relative min-h-36 overflow-hidden rounded-2xl border p-5 backdrop-blur-xl transition duration-300 hover:-translate-y-0.5 hover:border-fuchsia-400/30">
      <div className={`absolute right-4 top-4 h-20 w-20 rounded-full bg-gradient-to-br ${accents[accent]} opacity-20 blur-2xl transition group-hover:opacity-30`} />
      <div className="relative">
        <p className="theme-text-muted text-sm">{title}</p>
        <p className="theme-text-primary mt-4 text-4xl font-semibold tracking-tight">{value}</p>
        <p className="theme-text-faint mt-3 text-sm">{caption}</p>
      </div>
    </section>
  );
}
