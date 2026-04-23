import type { ManagedEnvironment } from '../types/api';

const CREATE_ENVIRONMENT_VALUE = '__create_environment__';

interface EnvironmentSwitcherProps {
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onCreateEnvironmentRequest: () => void;
  onManageEnvironmentRequest?: () => void;
  compact?: boolean;
}

export function EnvironmentSwitcher({
  environments,
  selectedEnvironmentId,
  onEnvironmentChange,
  onCreateEnvironmentRequest,
  onManageEnvironmentRequest,
  compact = false,
}: EnvironmentSwitcherProps) {
  return (
    <div className={`flex ${compact ? 'flex-row items-center gap-2' : 'flex-col gap-3 sm:flex-row sm:items-center sm:justify-between'}`}>
      <label className={`theme-inset flex items-center gap-3 rounded-2xl border ${compact ? 'h-10 px-3' : 'px-4 py-3'}`}>
        <span className="theme-text-faint text-[11px] font-semibold uppercase tracking-[0.18em]">Environment</span>
        <select
          value={selectedEnvironmentId}
          onChange={(event) => {
            if (event.target.value === CREATE_ENVIRONMENT_VALUE) {
              onCreateEnvironmentRequest();
              return;
            }
            onEnvironmentChange(event.target.value);
          }}
          className="theme-text-primary min-w-36 bg-transparent text-sm font-semibold outline-none"
          aria-label="Select environment"
        >
          {environments.map((environment) => (
            <option key={environment.environment_id} value={environment.environment_id}>
              {environment.name}
            </option>
          ))}
          <option value={CREATE_ENVIRONMENT_VALUE}>+ Create Environment</option>
        </select>
      </label>

      {onManageEnvironmentRequest ? (
        <button
          type="button"
          onClick={onManageEnvironmentRequest}
          className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition"
        >
          Manage
        </button>
      ) : null}
    </div>
  );
}
