import type { FormEvent } from 'react';
import { useMemo, useState } from 'react';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import { createEnvironment, deleteEnvironment, updateEnvironment } from '../services/api';
import type { EnvironmentCreateRequest, ManagedEnvironment, ManagedEnvironmentStatus, ManagedEnvironmentType } from '../types/api';

interface SettingsProps {
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onEnvironmentsChanged: (nextEnvironmentId?: string) => void;
}

interface EnvironmentFormState extends EnvironmentCreateRequest {}

const defaultFormState: EnvironmentFormState = {
  name: '',
  type: 'lab',
  description: '',
  status: 'active',
};

export function Settings({ environments, selectedEnvironmentId, onEnvironmentChange, onEnvironmentsChanged }: SettingsProps) {
  const [createForm, setCreateForm] = useState<EnvironmentFormState>(defaultFormState);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const editingEnvironment = useMemo(
    () => environments.find((environment) => environment.environment_id === editingId) ?? null,
    [editingId, environments],
  );

  async function handleCreateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const created = await createEnvironment(createForm);
      setCreateForm(defaultFormState);
      onEnvironmentChange(created.environment_id);
      onEnvironmentsChanged(created.environment_id);
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Unable to create environment');
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
    const payload: EnvironmentFormState = {
      name: String(formData.get('name') ?? ''),
      type: String(formData.get('type') ?? 'lab') as ManagedEnvironmentType,
      description: String(formData.get('description') ?? ''),
      status: String(formData.get('status') ?? 'active') as ManagedEnvironmentStatus,
    };
    setSaving(true);
    setError(null);
    try {
      const updated = await updateEnvironment(editingEnvironment.environment_id, payload);
      onEnvironmentChange(updated.environment_id);
      onEnvironmentsChanged(updated.environment_id);
      setEditingId(null);
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Unable to update environment');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(environmentId: string) {
    setSaving(true);
    setError(null);
    try {
      await deleteEnvironment(environmentId);
      const fallbackEnvironment = environments.find((environment) => environment.environment_id !== environmentId);
      if (selectedEnvironmentId === environmentId && fallbackEnvironment) {
        onEnvironmentChange(fallbackEnvironment.environment_id);
      }
      onEnvironmentsChanged(fallbackEnvironment?.environment_id);
      if (editingId === environmentId) {
        setEditingId(null);
      }
    } catch (errorValue) {
      setError(errorValue instanceof Error ? errorValue.message : 'Unable to delete environment');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {error ? <div className="theme-error rounded-2xl p-4 text-sm">{error}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
        <Panel title="Create Environment" eyebrow="Workspace Setup" description="Environments are now user-managed. Create them here, then switch between them throughout the app.">
          <form className="grid gap-4" onSubmit={handleCreateSubmit}>
            <input
              className="theme-input theme-focus rounded-2xl border px-4 py-3"
              name="name"
              placeholder="Environment name"
              value={createForm.name}
              onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))}
              required
            />
            <div className="grid gap-4 sm:grid-cols-2">
              <select
                className="theme-input theme-focus rounded-2xl border px-4 py-3"
                name="type"
                value={createForm.type}
                onChange={(event) => setCreateForm((current) => ({ ...current, type: event.target.value as ManagedEnvironmentType }))}
              >
                <option value="homelab">Homelab</option>
                <option value="lab">Lab</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
              <select
                className="theme-input theme-focus rounded-2xl border px-4 py-3"
                name="status"
                value={createForm.status}
                onChange={(event) => setCreateForm((current) => ({ ...current, status: event.target.value as ManagedEnvironmentStatus }))}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
            <textarea
              className="theme-input theme-focus min-h-32 rounded-2xl border px-4 py-3"
              name="description"
              placeholder="What this environment is for"
              value={createForm.description}
              onChange={(event) => setCreateForm((current) => ({ ...current, description: event.target.value }))}
              required
            />
            <button type="submit" disabled={saving} className="theme-button-primary rounded-2xl px-4 py-3 text-sm font-semibold transition disabled:opacity-60">
              {saving ? 'Saving...' : 'Create Environment'}
            </button>
          </form>
        </Panel>

        <Panel title="Environment Library" description="Edit or remove environments without relying on predefined options.">
          <div className="space-y-3">
            {environments.map((environment) => {
              const isEditing = editingEnvironment?.environment_id === environment.environment_id;
              return (
                <div key={environment.environment_id} className="theme-inset rounded-3xl border p-4">
                  {isEditing ? (
                    <form className="grid gap-3" onSubmit={handleUpdateSubmit}>
                      <input className="theme-input theme-focus rounded-2xl border px-4 py-3" name="name" defaultValue={environment.name} required />
                      <div className="grid gap-3 sm:grid-cols-2">
                        <select className="theme-input theme-focus rounded-2xl border px-4 py-3" name="type" defaultValue={environment.type}>
                          <option value="homelab">Homelab</option>
                          <option value="lab">Lab</option>
                          <option value="staging">Staging</option>
                          <option value="production">Production</option>
                        </select>
                        <select className="theme-input theme-focus rounded-2xl border px-4 py-3" name="status" defaultValue={environment.status}>
                          <option value="active">Active</option>
                          <option value="inactive">Inactive</option>
                        </select>
                      </div>
                      <textarea className="theme-input theme-focus min-h-24 rounded-2xl border px-4 py-3" name="description" defaultValue={environment.description} required />
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
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="theme-text-primary text-base font-semibold">{environment.name}</p>
                          <StatusBadge label={environment.type} tone="purple" />
                          <StatusBadge label={environment.status} tone={environment.status === 'active' ? 'cyan' : 'slate'} />
                          {selectedEnvironmentId === environment.environment_id ? <StatusBadge label="selected" tone="green" /> : null}
                        </div>
                        <p className="theme-text-muted mt-2 text-sm leading-6">{environment.description}</p>
                        <p className="theme-text-faint mt-3 text-xs">ID: {environment.environment_id}</p>
                      </div>
                      <div className="flex flex-wrap gap-3">
                        <button type="button" onClick={() => onEnvironmentChange(environment.environment_id)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
                          Select
                        </button>
                        <button type="button" onClick={() => setEditingId(environment.environment_id)} className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition">
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDelete(environment.environment_id)}
                          disabled={saving || environments.length === 1}
                          className="rounded-2xl border border-rose-400/30 px-4 py-2 text-sm font-semibold text-rose-300 transition disabled:opacity-40"
                        >
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
    </div>
  );
}
