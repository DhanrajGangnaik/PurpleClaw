import { useEffect, useState } from 'react';
import { Layout } from '../../components/layout/Layout';
import { PageLoading, MetricCard } from '../../components/ui';
import { getAssets } from '../../services/api';
import type { Asset } from '../../services/api';
import { Network as NetworkIcon } from 'lucide-react';

export function Network() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAssets(1, 100).then((d) => setAssets(d.items)).finally(() => setLoading(false));
  }, []);

  const byType = assets.reduce((acc, a) => { acc[a.asset_type] = (acc[a.asset_type] ?? 0) + 1; return acc; }, {} as Record<string, number>);

  return (
    <Layout title="Network">
      <div className="space-y-5">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(byType).slice(0, 4).map(([type, count]) => (
            <MetricCard key={type} label={type.replace(/_/g, ' ')} value={count} color="blue" />
          ))}
        </div>

        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <NetworkIcon className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-gray-300">Network Topology</h2>
          </div>
          {loading ? <PageLoading /> : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {assets.filter((a) => a.asset_type === 'network_device' || a.asset_type === 'firewall').map((a) => (
                <div key={a.id} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-3 h-3 rounded-full ${a.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium text-gray-200 text-sm">{a.hostname}</span>
                    <span className="ml-auto font-mono text-xs text-gray-500">{a.ip_address}</span>
                  </div>
                  <div className="flex gap-4 text-xs text-gray-600">
                    <span>Type: {a.asset_type}</span>
                    <span>Owner: {a.owner}</span>
                    <span>Risk: {a.risk_score}</span>
                  </div>
                  {Array.isArray(a.asset_metadata?.ports) && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {(a.asset_metadata.ports as number[]).slice(0, 6).map((p) => (
                        <span key={p} className="badge badge-info text-xs">{String(p)}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
