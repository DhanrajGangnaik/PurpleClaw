import { MetricCard } from '../../MetricCard';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { MetricCardWidgetPayload } from '../../../types/api';

interface MetricCardWidgetProps {
  widget: MetricCardWidgetPayload;
}

export function MetricCardWidget({ widget }: MetricCardWidgetProps) {
  if (!widget.data) {
    return <WidgetEmptyState message="Metric data is unavailable." />;
  }

  return <MetricCard title={widget.title ?? 'Metric'} value={widget.data.value} caption={widget.data.caption ?? 'No caption'} accent="cyan" />;
}
