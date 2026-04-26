import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, EmptyState } from '../../components/ui';
import { getSystemSettings } from '../../services/api';
import { Settings } from 'lucide-react';

export function SystemSettings() {
  const [settings, setSettings] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSystemSettings().then(setSettings).finally(() => setLoading(false));
  }, []);

  return (
    <Layout title="System Settings">
      <div className="card">
        <div className="p-4 border-b border-gray-800 flex items-center gap-2">
          <Settings className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-gray-300">System Configuration</h2>
        </div>
        {loading ? <PageLoading /> : settings.length === 0 ? <EmptyState title="No settings" /> : (
          <div className="divide-y divide-gray-800">
            {settings.map((s, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-300">{String(s.key).replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}</p>
                  <p className="text-xs text-gray-600">{String(s.description ?? '')}</p>
                </div>
                <div className="text-sm text-purple-300 font-mono bg-gray-800 px-3 py-1 rounded-lg">{String(s.value)}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
