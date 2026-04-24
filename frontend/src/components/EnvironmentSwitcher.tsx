import { useEffect, useId, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import type { ManagedEnvironment } from '../types/api';

interface EnvironmentSwitcherProps {
  environments: ManagedEnvironment[];
  selectedEnvironmentId: string;
  onEnvironmentChange: (environmentId: string) => void;
  onManageEnvironmentRequest?: () => void;
  compact?: boolean;
}

function EnvironmentGlyph() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="5" rx="1.5" />
      <rect x="3" y="10.5" width="18" height="5" rx="1.5" />
      <rect x="3" y="17" width="18" height="3" rx="1.5" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 160ms ease' }}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

export function EnvironmentSwitcher({
  environments,
  selectedEnvironmentId,
  onEnvironmentChange,
  onManageEnvironmentRequest,
  compact = false,
}: EnvironmentSwitcherProps) {
  const [open, setOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const menuId = useId();

  const selectedEnvironment = environments.find((environment) => environment.environment_id === selectedEnvironmentId) ?? environments[0] ?? null;

  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }

    window.addEventListener('mousedown', handlePointerDown);
    window.addEventListener('keydown', handleEscape);
    return () => {
      window.removeEventListener('mousedown', handlePointerDown);
      window.removeEventListener('keydown', handleEscape);
    };
  }, [open]);

  useEffect(() => {
    const selectedIndex = Math.max(0, environments.findIndex((environment) => environment.environment_id === selectedEnvironmentId));
    setHighlightedIndex(selectedIndex);
  }, [environments, selectedEnvironmentId]);

  const wrapperClass = compact ? 'min-w-[220px]' : 'w-full sm:min-w-[320px]';

  function handleMenuKeyDown(event: ReactKeyboardEvent<HTMLButtonElement>) {
    if (environments.length === 0) {
      if (!open && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault();
        setOpen(true);
      }
      return;
    }

    if (!open && (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      setOpen(true);
      return;
    }

    if (!open) {
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setHighlightedIndex((current) => (current + 1) % environments.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlightedIndex((current) => (current - 1 + environments.length) % environments.length);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      const target = environments[highlightedIndex];
      if (target) {
        onEnvironmentChange(target.environment_id);
        setOpen(false);
      }
    }
  }

  return (
    <div ref={rootRef} className={`relative ${wrapperClass}`}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((current) => !current)}
        onKeyDown={handleMenuKeyDown}
        className="flex w-full items-center justify-between gap-3 rounded-2xl border px-3 py-2.5 text-left transition"
        style={{ background: 'var(--bg-card)', borderColor: open ? 'var(--border-focus)' : 'var(--border)', color: 'var(--text-primary)' }}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={menuId}
      >
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border" style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)', color: 'var(--status-info)' }}>
            <EnvironmentGlyph />
          </div>
          <div className="min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em]" style={{ color: 'var(--text-muted)' }}>Environment</p>
            <p className="truncate text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
              {selectedEnvironment?.name ?? 'No Environment'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {selectedEnvironment ? (
            <span className="hidden rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] sm:inline-flex" style={{ borderColor: 'var(--border)', color: 'var(--text-muted)' }}>
              {selectedEnvironment.type}
            </span>
          ) : null}
          <span style={{ color: 'var(--text-muted)' }}>
            <ChevronIcon open={open} />
          </span>
        </div>
      </button>

      {open ? (
        <div
          id={menuId}
          role="menu"
          aria-label="Environment selector"
          className="absolute right-0 top-[calc(100%+0.5rem)] z-40 w-full overflow-hidden rounded-2xl border shadow-[var(--shadow-card)]"
          style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}
        >
          <div className="max-h-80 overflow-y-auto p-2">
            {environments.map((environment, index) => {
              const isSelected = environment.environment_id === selectedEnvironmentId;
              const isHighlighted = index === highlightedIndex;

              return (
                <button
                  key={environment.environment_id}
                  type="button"
                  role="menuitemradio"
                  aria-checked={isSelected}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  onClick={() => {
                    onEnvironmentChange(environment.environment_id);
                    setOpen(false);
                  }}
                  className="flex w-full items-center justify-between gap-3 rounded-xl px-3 py-3 text-left transition"
                  style={{
                    background: isSelected
                      ? 'rgba(0, 143, 236, 0.10)'
                      : isHighlighted
                        ? 'var(--bg-elevated)'
                        : 'transparent',
                    color: 'var(--text-primary)',
                  }}
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border" style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)', color: isSelected ? 'var(--status-info)' : 'var(--text-muted)' }}>
                      <EnvironmentGlyph />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold">{environment.name}</p>
                      <p className="truncate text-xs" style={{ color: 'var(--text-muted)' }}>
                        {environment.description || environment.type}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedEnvironmentId === environment.environment_id ? (
                      <span className="rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.12em]" style={{ borderColor: 'rgba(62, 189, 65, 0.22)', color: 'var(--status-success)' }}>
                        Active
                      </span>
                    ) : null}
                    {isSelected ? (
                      <span style={{ color: 'var(--status-info)' }}>
                        <CheckIcon />
                      </span>
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>

          <div className="border-t p-2" style={{ borderColor: 'var(--border)', background: 'var(--bg-elevated)' }}>
            {onManageEnvironmentRequest ? (
              <button
                type="button"
                onClick={() => {
                  setOpen(false);
                  onManageEnvironmentRequest();
                }}
                className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm font-semibold transition"
                style={{ color: 'var(--text-primary)' }}
              >
                <span>Manage Environments</span>
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
