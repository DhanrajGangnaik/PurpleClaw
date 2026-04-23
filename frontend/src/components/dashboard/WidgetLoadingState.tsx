export function WidgetLoadingState() {
  return (
    <div className="theme-inset rounded-2xl border p-4">
      <div className="animate-pulse space-y-3">
        <div className="h-4 w-32 rounded bg-white/10" />
        <div className="h-10 rounded bg-white/5" />
        <div className="h-10 rounded bg-white/5" />
      </div>
    </div>
  );
}
