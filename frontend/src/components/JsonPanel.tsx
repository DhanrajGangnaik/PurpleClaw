interface JsonPanelProps {
  value: unknown;
  emptyText?: string;
  className?: string;
}

export function JsonPanel({ value, emptyText = 'No response yet.', className = '' }: JsonPanelProps) {
  return (
    <pre className={`theme-code overflow-auto rounded-2xl border p-4 font-mono text-xs leading-6 shadow-inner ${className}`}>
      {value ? JSON.stringify(value, null, 2) : emptyText}
    </pre>
  );
}
