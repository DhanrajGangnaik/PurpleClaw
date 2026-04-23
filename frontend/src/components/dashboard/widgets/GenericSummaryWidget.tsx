import { JsonPanel } from '../../JsonPanel';
import { WidgetEmptyState } from '../WidgetEmptyState';
import type { GenericSummaryWidgetPayload } from '../../../types/api';

interface GenericSummaryWidgetProps {
  widget: GenericSummaryWidgetPayload;
}

export function GenericSummaryWidget({ widget }: GenericSummaryWidgetProps) {
  if (!widget.data || Object.keys(widget.data).length === 0) {
    return <WidgetEmptyState message="No summary data is available." />;
  }
  return <JsonPanel value={widget.data} emptyText="No summary data is available." />;
}
