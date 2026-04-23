import { useMemo, useState } from 'react';
import { DataTable, type DataColumn } from '../components/DataTable';
import { JsonPanel } from '../components/JsonPanel';
import { useFetch } from '../hooks/useFetch';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { generateReport, getReportDownloadUrl, previewReport } from '../services/api';
import type { DashboardConfig, Report, ReportPreview, ReportTemplate, ScanDetail } from '../types/api';
import { formatDate } from '../utils';

interface ReportsProps {
  selectedEnvironmentId: string;
  reports: Report[];
  templates: ReportTemplate[];
  scans: ScanDetail[];
  dashboards: DashboardConfig[];
  loading: boolean;
  error: string | null;
  onDataChanged: () => void;
}

function tone(status: Report['status']) {
  return status === 'ready' ? 'green' : 'red';
}

export function Reports({ selectedEnvironmentId, reports, templates, scans, dashboards, loading, error, onDataChanged }: ReportsProps) {
  const [title, setTitle] = useState('Environment Assessment');
  const [generatedFrom, setGeneratedFrom] = useState<Report['generated_from']>('environment_summary');
  const [sourceId, setSourceId] = useState('');
  const [templateId, setTemplateId] = useState(templates[0]?.template_id ?? 'default-assessment');
  const [actionError, setActionError] = useState<string | null>(null);
  const [selectedReportId, setSelectedReportId] = useState<string>('');
  const [generating, setGenerating] = useState(false);

  const visibleReports = useMemo(
    () => reports.filter((report) => report.environment_id === selectedEnvironmentId),
    [reports, selectedEnvironmentId],
  );
  const selectedReport = visibleReports.find((report) => report.report_id === selectedReportId) ?? visibleReports[0] ?? null;
  const availableSources =
    generatedFrom === 'scan'
      ? scans.filter((scan) => scan.request.environment_id === selectedEnvironmentId).map((scan) => ({ id: scan.request.scan_id, label: `${scan.request.target} - ${scan.request.status}` }))
      : generatedFrom === 'dashboard'
        ? dashboards.filter((dashboard) => dashboard.environment_id === selectedEnvironmentId).map((dashboard) => ({ id: dashboard.dashboard_id, label: dashboard.name }))
      : [];
  const previewFetch = useFetch(
    () =>
      previewReport({
        environment_id: selectedEnvironmentId,
        title,
        generated_from: generatedFrom,
        source_id: sourceId || null,
        template_id: templateId || null,
      }),
    [selectedEnvironmentId, title, generatedFrom, sourceId, templateId],
  );

  const columns: DataColumn<Report>[] = [
    { key: 'title', label: 'Report', render: (report) => <span className="theme-text-primary font-medium">{report.title}</span> },
    { key: 'type', label: 'Generated From', render: (report) => <StatusBadge label={report.generated_from} tone="purple" /> },
    { key: 'status', label: 'Status', render: (report) => <StatusBadge label={report.status} tone={tone(report.status)} /> },
    { key: 'generated', label: 'Generated', render: (report) => formatDate(report.generated_at) },
    {
      key: 'download',
      label: 'Download',
      render: (report) =>
        report.status === 'ready' ? (
          <a href={getReportDownloadUrl(report.report_id)} className="theme-brand text-sm font-semibold underline underline-offset-4">
            PDF
          </a>
        ) : (
          <span className="theme-text-faint text-sm">Unavailable</span>
        ),
    },
  ];

  const handleGenerate = async () => {
    setGenerating(true);
    setActionError(null);
    try {
      await generateReport({
        environment_id: selectedEnvironmentId,
        title,
        generated_from: generatedFrom,
        source_id: sourceId || null,
        template_id: templateId || null,
      });
      onDataChanged();
    } catch (actionValue) {
      setActionError(actionValue instanceof Error ? actionValue.message : 'Unable to generate report');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <Panel title="Generate Report" eyebrow="Industry Style PDF">
        {(error || actionError) && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error ?? actionError}</div>}
        <div className="grid gap-4 xl:grid-cols-2">
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Title</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3" placeholder="Quarterly Environment Assessment" />
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Template</span>
            <select value={templateId} onChange={(event) => setTemplateId(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3">
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Generate From</span>
            <select value={generatedFrom} onChange={(event) => setGeneratedFrom(event.target.value as Report['generated_from'])} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3">
              <option value="environment_summary">environment_summary</option>
              <option value="findings">findings</option>
              <option value="scan">scan</option>
              <option value="dashboard">dashboard</option>
            </select>
          </label>
          <label className="space-y-2">
            <span className="theme-text-faint text-xs font-bold uppercase tracking-[0.18em]">Source</span>
            <select value={sourceId} onChange={(event) => setSourceId(event.target.value)} className="theme-input theme-focus w-full rounded-2xl border px-4 py-3" disabled={availableSources.length === 0}>
              <option value="">No explicit source</option>
              {availableSources.map((source) => (
                <option key={source.id} value={source.id}>
                  {source.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" onClick={handleGenerate} disabled={generating || !title.trim()} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold">
            {generating ? 'Generating...' : 'Generate Report'}
          </button>
          <button type="button" onClick={() => void previewFetch.refetch()} className="theme-button-secondary rounded-2xl px-4 py-3 text-sm font-semibold">
            Preview Report
          </button>
          {templateId && <StatusBadge label={templateId} tone="cyan" />}
        </div>
      </Panel>

      <Panel title="Generated Reports" eyebrow="Downloadable PDFs">
        {loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Loading reports from PurpleClaw...</div>
        ) : (
          <DataTable columns={columns} rows={visibleReports} getRowKey={(report) => report.report_id} emptyText="No reports returned by the API." onRowClick={(report) => setSelectedReportId(report.report_id)} />
        )}
      </Panel>

      <Panel title="Report Detail" eyebrow="Metadata">
        <JsonPanel value={selectedReport} emptyText="Select a generated report to inspect its metadata and source context." />
      </Panel>

      <Panel title="Report Preview" eyebrow="Rendered Sections">
        {previewFetch.loading ? (
          <div className="theme-text-faint py-14 text-center text-sm">Rendering report preview...</div>
        ) : previewFetch.data ? (
          <div className="space-y-4">
            {(previewFetch.data as ReportPreview).sections.map((section) => (
              <div key={section.name} className="theme-inset rounded-2xl border p-4">
                <div className="theme-text-primary font-medium">{section.name}</div>
                <div className="mt-3">
                  <JsonPanel value={section.content} emptyText="No content returned for this section." />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="theme-text-faint py-14 text-center text-sm">Generate a preview to inspect the rendered report before downloading the PDF.</div>
        )}
      </Panel>
    </div>
  );
}
