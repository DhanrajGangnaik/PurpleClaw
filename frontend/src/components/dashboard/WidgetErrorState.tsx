interface WidgetErrorStateProps {
  message: string;
}

export function WidgetErrorState({ message }: WidgetErrorStateProps) {
  return <div className="theme-error rounded-2xl p-4 text-sm">{message}</div>;
}
