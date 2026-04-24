import type { FormEvent } from 'react';
import { useMemo, useState } from 'react';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { createEnvironment, deleteEnvironment, getErrorMessage, updateEnvironment } from '../services/api';
import type { ManagedEnvironment } from '../types/api';
import { formatDate } from '../utils';

interface SettingsProps {
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onEnvironmentsChanged: (nextEnvironmentId?: string) => void;
}

interface CreateEnvironmentFormState {
  name: string;
  description: string;
}

const defaultFormState: CreateEnvironmentFormState = {
  name: '',
  description: '',
};

export function Settings({ environments, selectedEnvironmentId, onEnvironmentChange, onEnvironmentsChanged }: SettingsProps) {
  const [createForm, setCreateForm] = useState<CreateEnvironmentFormState>(defaultFormState);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const editingEnvironment = useMemo(
    () => environments.find((environment) => environment.environment_id === editingId) ?? null,
    [editingId, environments],
  );
  const pendingDeleteEnvironment = useMemo(
    () => environments.find((environment) => environment.environment_id === pendingDeleteId) ?? null,
    [environments, pendingDeleteId],
  );

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const trimmedName = createForm.name.trim();
      const trimmedDescription = createForm.description.trim();
      const created = await createEnvironment({
        name: trimmedName,
        description: trimmedDescription || '',
      });
      setCreateForm(defaultFormState);
      onEnvironmentChange(created.environment_id);
      onEnvironmentsChanged(created.environment_id);
      setSuccess(`Environment "${created.name}" created.`);
    } catch (errorValue) {
      setError(getErrorMessage(errorValue));
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingEnvironment) {
      return;
    }
    const formData = new FormData(event.currentTarget);
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateEnvironment(editingEnvironment.environment_id, {
        name: String(formData.get('name') ?? ''),
        description: String(formData.get('description') ?? ''),
        type: editingEnvironment.type,
        status: editingEnvironment.status,
      });
      onEnvironmentChange(updated.environment_id);
      onEnvironmentsChanged(updated.environment_id);
      setEditingId(null);
      setSuccess(`Environment "${updated.name}" updated.`);
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Unable to update environment');
    } finally {
      setSaving(false);
    }
  }

  async function confirmDelete() {
    if (!pendingDeleteEnvironment) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const fallbackEnvironment = environments.find((environment) => environment.environment_id !== pendingDeleteEnvironment.environment_id);
      const deletedSelectedEnvironment = selectedEnvironmentId === pendingDeleteEnvironment.environment_id;
      await deleteEnvironment(pendingDeleteEnvironment.environment_id);
      if (deletedSelectedEnvironment) {
        if (fallbackEnvironment) {
          onEnvironmentChange(fallbackEnvironment.environment_id);
        } else {
          onEnvironmentChange('');
        }
      }
      onEnvironmentsChanged(
        deletedSelectedEnvironment
          ? (fallbackEnvironment?.environment_id ?? '')
          : selectedEnvironmentId,
      );
      if (editingId === pendingDeleteEnvironment.environment_id) {
        setEditingId(null);
      }
      setSuccess(`Environment "${pendingDeleteEnvironment.name}" deleted.`);
      setPendingDeleteId(null);
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Unable to delete environment');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {error ? <div className="theme-error rounded-2xl p-4 text-sm">{error}</div> : null}
      {success ? <div className="theme-success-banner rounded-2xl p-4 text-sm">{success}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
        <Panel title="Create Environment" eyebrow="Workspace Setup" description="Create environments with a name and an optional description. No defaults are recreated automatically.">
          <form className="grid gap-4" onSubmit={handleCreateSubmit}>
            <input
              className="theme-input theme-focus rounded-2xl px-4 py-3"
              name="name"
              placeholder="Environment name"
              value={createForm.name}
              onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <textarea
              className="theme-input theme-focus min-h-32 rounded-2xl px-4 py-3"
              name="description"
              placeholder="Optional description"
              value={createForm.description}
              onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
            />
            <button type="submit" disabled={saving} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold transition disabled:opacity-60">
              {saving ? 'Saving...' : 'Create Environment'}
            </button>
          </form>
        </Panel>

        <Panel title="Environment Library" eyebrow="Available Contexts" description={environments.length ? 'Each environment can be selected, edited, or deleted.' : 'No environments yet. Create one to begin.'}>
          <div className="space-y-3">
            {!environments.length ? (
              <div className="theme-text-faint py-12 text-center text-sm">No environments yet. Create one to begin.</div>
            ) : null}
            {environments.map((environment) => {
              const isEditing = editingEnvironment?.environment_id === environment.environment_id;
              const isSelected = selectedEnvironmentId === environment.environment_id;

              return (
                <div key={environment.environment_id} className="theme-inset rounded-3xl p-4">
                  {isEditing ? (
                    <form className="grid gap-3" onSubmit={handleUpdateSubmit}>
                      <input className="theme-input theme-focus rounded-2xl px-4 py-3" name="name" defaultValue={environment.name} required />
                      <textarea className="theme-input theme-focus min-h-24 rounded-2xl px-4 py-3" name="description" defaultValue={environment.description} placeholder="Optional description" />
                      <div className="flex flex-wrap gap-3">
                        <button type="submit" disabled={saving} className="theme-button-primary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:opacity-60">
                          Save Changes
                        </button>
                        <button type="button" onClick={() => setEditingId(null)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
                          Cancel
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="theme-text-primary text-base font-semibold">{environment.name}</p>
                          <StatusBadge label={environment.type} tone="purple" />
                          <StatusBadge label={environment.status} tone={environment.status === 'active' ? 'cyan' : 'slate'} />
                          {isSelected ? <StatusBadge label="selected" tone="green" /> : null}
                        </div>
                        <p className="theme-text-muted mt-2 text-sm leading-6">{environment.description || 'No description provided.'}</p>
                        <div className="mt-3 flex flex-wrap gap-4 text-xs" style={{ color: 'var(--text-muted)' }}>
                          <span>Created {formatDate(environment.created_at)}</span>
                          <span>Updated {formatDate(environment.updated_at)}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <button type="button" onClick={() => onEnvironmentChange(environment.environment_id)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
                          Select
                        </button>
                        <button type="button" onClick={() => setEditingId(environment.environment_id)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
                          Edit
                        </button>
                        <button type="button" onClick={() => setPendingDeleteId(environment.environment_id)} disabled={saving} className="theme-button-danger rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:opacity-40">
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      {pendingDeleteEnvironment ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4 backdrop-blur-sm">
          <div className="workspace-panel w-full max-w-xl p-6">
            <p className="workspace-eyebrow">Confirm Deletion</p>
            <h3 className="mt-2 text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
              Delete {pendingDeleteEnvironment.name}?
            </h3>
            <p className="mt-3 text-sm leading-6" style={{ color: 'var(--text-muted)' }}>
              Deleting this environment will remove its dashboards, data sources, scans, reports, and environment-scoped records.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button type="button" onClick={confirmDelete} disabled={saving} className="theme-button-danger rounded-2xl px-4 py-3 text-sm font-semibold">
                {saving ? 'Deleting...' : 'Delete Environment'}
              </button>
              <button type="button" onClick={() => setPendingDeleteId(null)} className="theme-button-secondary rounded-2xl px-4 py-3 text-sm font-semibold">
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
