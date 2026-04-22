import { useState } from 'react';
import { JsonPanel } from '../components/JsonPanel';
import { Panel } from '../components/Panel';
import { StatusBadge } from '../components/StatusBadge';
import {
  defaultPlan,
  executeStub,
  getErrorMessage,
  validatePlan,
  type ExercisePlan,
  type ExecuteResponse,
  type ValidationResult,
} from '../services/api';

interface ValidatorProps {
  selectedEnvironmentId: string;
  onDataChanged: () => void;
}

type ResponsePayload = ValidationResult | ExecuteResponse | null;

export function Validator({ selectedEnvironmentId, onDataChanged }: ValidatorProps) {
  const [payload, setPayload] = useState(JSON.stringify(defaultPlan, null, 2));
  const [response, setResponse] = useState<ResponsePayload>(null);
  const [mode, setMode] = useState<'idle' | 'validating' | 'executing'>('idle');
  const [error, setError] = useState<string | null>(null);

  function parsePayload() {
    return JSON.parse(payload) as ExercisePlan;
  }

  async function handleValidate() {
    setMode('validating');
    setError(null);
    try {
      const plan = parsePayload();
      const result = await validatePlan(plan, selectedEnvironmentId);
      setResponse(result);
      onDataChanged();
    } catch (validationError) {
      const message = validationError instanceof SyntaxError ? validationError.message : getErrorMessage(validationError);
      setError(message);
    } finally {
      setMode('idle');
    }
  }

  async function handleExecute() {
    setMode('executing');
    setError(null);
    try {
      const plan = parsePayload();
      const result = await executeStub(plan, selectedEnvironmentId);
      setResponse(result);
      onDataChanged();
    } catch (executionError) {
      const message = getErrorMessage(executionError);
      setError(message);
    } finally {
      setMode('idle');
    }
  }

  const responseValid = response && 'valid' in response ? response.valid : response && 'execution_id' in response;

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <Panel
        title="ExercisePlan JSON"
        eyebrow="Editor"
        action={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleValidate}
              disabled={mode !== 'idle'}
              className="theme-button-primary rounded-2xl px-4 py-2 text-sm font-semibold transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {mode === 'validating' ? 'Validating...' : 'Validate Plan'}
            </button>
            <button
              type="button"
              onClick={handleExecute}
              disabled={mode !== 'idle'}
              className="theme-button-secondary rounded-2xl px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50"
            >
              {mode === 'executing' ? 'Recording...' : 'Record Result'}
            </button>
          </div>
        }
      >
        <textarea
          value={payload}
          onChange={(event) => setPayload(event.target.value)}
          spellCheck={false}
          className="theme-code theme-focus min-h-[620px] w-full resize-y rounded-2xl border p-4 font-mono text-sm leading-6 transition"
        />
      </Panel>

      <div className="space-y-6">
        <Panel title="Validation Result" eyebrow="Structured Response">
          {error && <div className="theme-error mb-4 rounded-2xl p-4 text-sm">{error}</div>}
          <div className="mb-4 flex items-center gap-3">
            <StatusBadge label={responseValid ? 'success' : response ? 'invalid' : 'waiting'} tone={responseValid ? 'green' : response ? 'red' : 'slate'} />
            <span className="theme-text-faint text-sm">Review the validation outcome before recording verification results.</span>
          </div>
          <JsonPanel value={response} className="max-h-[420px]" />
        </Panel>
      </div>
    </div>
  );
}
