import { Card } from '../Card';

export interface WidgetDefinition {
  type: string;
  label: string;
  description: string;
  category: 'kpi' | 'analysis' | 'secondary';
}

interface WidgetSelectorModalProps {
  open: boolean;
  definitions: WidgetDefinition[];
  onClose: () => void;
  onSelect: (definition: WidgetDefinition) => void;
}

const categoryLabels: Record<WidgetDefinition['category'], string> = {
  kpi: 'KPI Widgets',
  analysis: 'Primary Analysis',
  secondary: 'Secondary Context',
};

export function WidgetSelectorModal({ open, definitions, onClose, onSelect }: WidgetSelectorModalProps) {
  if (!open) {
    return null;
  }

  const categories: WidgetDefinition['category'][] = ['kpi', 'analysis', 'secondary'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4">
      <Card className="w-full max-w-4xl p-6">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="theme-text-faint text-[11px] font-semibold uppercase tracking-[0.18em]">Dashboard Builder</p>
            <h3 className="theme-text-primary mt-1 text-xl font-semibold">Add Widget</h3>
            <p className="theme-text-muted mt-2 text-sm">Choose a widget type, then configure its title, data source, and display settings in the builder.</p>
          </div>
          <button type="button" onClick={onClose} className="theme-button-secondary rounded-xl px-3 py-2 text-sm font-medium">
            Close
          </button>
        </div>

        <div className="space-y-6">
          {categories.map((category) => {
            const items = definitions.filter((definition) => definition.category === category);
            if (items.length === 0) {
              return null;
            }
            return (
              <div key={category} className="space-y-3">
                <div>
                  <p className="theme-text-primary text-sm font-semibold">{categoryLabels[category]}</p>
                  <div className="theme-divider mt-2" />
                </div>
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {items.map((definition) => (
                    <button
                      key={definition.type}
                      type="button"
                      onClick={() => onSelect(definition)}
                      className="theme-inset theme-focus rounded-card border p-4 text-left transition hover:border-slate-400/70"
                    >
                      <p className="theme-text-primary text-sm font-semibold">{definition.label}</p>
                      <p className="theme-text-muted mt-2 text-sm leading-6">{definition.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
