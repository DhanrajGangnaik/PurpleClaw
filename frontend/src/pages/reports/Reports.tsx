import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, StatusBadge, MetricCard, Pagination, EmptyState } from '../../components/ui';
import { getReports, getReportTemplates, generateReport } from '../../services/api';
import type { GeneratedReport, ReportTemplate, Paginated } from '../../services/api';
import { FileBarChart2, Plus } from 'lucide-react';
import toast from 'react-hot-toast';

export function Reports() {
  const [data, setData] = useState<Paginated<GeneratedReport> | null>(null);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [reportTitle, setReportTitle] = useState('');

  const load = () => {
    setLoading(true);
    Promise.all([getReports(page, 25), getReportTemplates()])
      .then(([r, t]) => { setData(r); setTemplates(t); })
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); }, [page]);

  const generate = async () => {
    if (!reportTitle) { toast.error('Enter a report title'); return; }
    setGenerating(true);
    try {
      await generateReport({ title: reportTitle, report_type: 'executive', template_id: selectedTemplate ? Number(selectedTemplate) : undefined });
      toast.success('Report generated');
      setReportTitle('');
      load();
    } catch { toast.error('Generation failed'); }
    finally { setGenerating(false); }
  };

  return (
    <Layout title="Reports">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard label="Total Reports" value={data?.total ?? 0} color="purple" />
          <MetricCard label="Templates" value={templates.length} color="blue" />
          <MetricCard label="Generated Today" value={data?.items.filter((r) => r.created_at.startsWith(new Date().toISOString().slice(0, 10))).length ?? 0} color="green" />
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Generate New Report</h3>
          <div className="flex gap-3 flex-wrap">
            <input value={reportTitle} onChange={(e) => setReportTitle(e.target.value)} placeholder="Report title..." className="flex-1 min-w-48" />
            <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)} className="w-48">
              <option value="">No template</option>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            <button onClick={generate} disabled={generating} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" /> {generating ? 'Generating…' : 'Generate'}
            </button>
          </div>
        </div>

        <div className="card">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <FileBarChart2 className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold text-gray-300">Generated Reports</h2>
          </div>
          {loading ? <PageLoading /> : data?.items.length === 0 ? <EmptyState icon={<FileBarChart2 className="w-10 h-10" />} title="No reports generated" /> : (
            <div className="table-wrapper">
              <table>
                <thead><tr><th>Title</th><th>Type</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {data?.items.map((r) => (
                    <tr key={r.id}>
                      <td className="font-medium text-gray-200">{r.title}</td>
                      <td><span className="badge badge-purple">{r.report_type}</span></td>
                      <td><StatusBadge status={r.status} /></td>
                      <td className="text-gray-600 text-xs">{new Date(r.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="px-4 pb-4"><Pagination page={page} pages={data?.pages ?? 1} onChange={setPage} /></div>
        </div>
      </div>
    </Layout>
  );
}
