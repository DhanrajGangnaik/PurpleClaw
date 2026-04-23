import type { ReactElement } from 'react';
import { WidgetCard } from '../../components/dashboard/WidgetCard';
import { WidgetEmptyState } from '../../components/dashboard/WidgetEmptyState';
import { WidgetErrorState } from '../../components/dashboard/WidgetErrorState';
import { FindingsTableWidget } from '../../components/dashboard/widgets/FindingsTableWidget';
import { GenericSummaryWidget } from '../../components/dashboard/widgets/GenericSummaryWidget';
import { MetricCardWidget } from '../../components/dashboard/widgets/MetricCardWidget';
import { ReportListWidget } from '../../components/dashboard/widgets/ReportListWidget';
import { RiskyAssetsWidget } from '../../components/dashboard/widgets/RiskyAssetsWidget';
import { ServiceHealthWidget } from '../../components/dashboard/widgets/ServiceHealthWidget';
import { TelemetrySummaryWidget } from '../../components/dashboard/widgets/TelemetrySummaryWidget';
import { VulnerabilitiesSummaryWidget } from '../../components/dashboard/widgets/VulnerabilitiesSummaryWidget';
import type { RenderedWidget } from '../../types/api';

interface RegistryEntry {
  render: (widget: RenderedWidget) => ReactElement;
}

const registry: Record<string, RegistryEntry> = {
  metric_card: { render: (widget) => <MetricCardWidget widget={widget as never} /> },
  findings_table: { render: (widget) => <FindingsTableWidget widget={widget as never} /> },
  risky_assets: { render: (widget) => <RiskyAssetsWidget widget={widget as never} /> },
  telemetry_summary: { render: (widget) => <TelemetrySummaryWidget widget={widget as never} /> },
  vulnerabilities_summary: { render: (widget) => <VulnerabilitiesSummaryWidget widget={widget as never} /> },
  service_health: { render: (widget) => <ServiceHealthWidget widget={widget as never} /> },
  report_list: { render: (widget) => <ReportListWidget widget={widget as never} /> },
  alerts_summary: { render: (widget) => <GenericSummaryWidget widget={widget as never} /> },
  signals_summary: { render: (widget) => <GenericSummaryWidget widget={widget as never} /> },
};

export function renderDashboardWidget(widget: RenderedWidget) {
  const entry = registry[widget.type];
  if (!entry) {
    return (
      <WidgetCard title={widget.title ?? 'Unsupported Widget'} type={widget.type} freshness={widget.freshness} lastUpdated={widget.last_updated}>
        <WidgetEmptyState message={`Widget type ${widget.type} is not supported by the current renderer.`} />
      </WidgetCard>
    );
  }
  try {
    return (
      <WidgetCard title={widget.title ?? 'Widget'} type={widget.type} freshness={widget.freshness} lastUpdated={widget.last_updated}>
        {entry.render(widget)}
      </WidgetCard>
    );
  } catch (error) {
    return (
      <WidgetCard title={widget.title ?? 'Widget'} type={widget.type} freshness={widget.freshness} lastUpdated={widget.last_updated}>
        <WidgetErrorState message={error instanceof Error ? error.message : 'Widget failed to render.'} />
      </WidgetCard>
    );
  }
}
