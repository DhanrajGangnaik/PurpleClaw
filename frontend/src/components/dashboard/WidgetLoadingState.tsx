export function WidgetLoadingState() {
  return (
    <div className="theme-inset rounded-2xl p-4">
      <div className="animate-pulse space-y-3">
        <div className="h-4 w-32 rounded" style={{ background: 'var(--border-strong)' }} />
        <div className="h-10 rounded" style={{ background: 'var(--border)' }} />
        <div className="h-10 rounded" style={{ background: 'var(--border)' }} />
      </div>
    </div>
  );
}
