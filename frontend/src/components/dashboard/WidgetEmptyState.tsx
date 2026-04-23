interface WidgetEmptyStateProps {
  message: string;
}

export function WidgetEmptyState({ message }: WidgetEmptyStateProps) {
  return <div className="theme-text-faint rounded-2xl border border-dashed px-4 py-10 text-center text-sm">{message}</div>;
}
