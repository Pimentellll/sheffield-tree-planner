import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, CanopyClient } from '../api/client'
import type { AgentRun, AgentStatus } from '../api/types'
import { MAX_GOAL, availability, goalError, isRunning, runView, uncitedRuns } from '../planning/agent'
import type { Workspace } from '../planning/useWorkspace'

const client = new CanopyClient()
const DEFAULT_GOAL = 'Evaluate the current proposal and explain the computed additional shade.'
const short = (value: string, n = 12) => (value.length > n + 1 ? `${value.slice(0, n)}…` : value)
const errorText = (err: unknown) => (err instanceof ApiError ? err.message : err instanceof Error ? err.message : String(err))

/**
 * Server-side planning agent over the accepted task. The browser only asks the API to start,
 * read or stop a run; it never calls the model and offers no way for the agent to accept.
 */
export function AgentPanel({ ws }: { ws: Workspace }) {
  const [status, setStatus] = useState<AgentStatus | null>(null)
  const [statusError, setStatusError] = useState<string | null>(null)
  const [goal, setGoal] = useState(DEFAULT_GOAL)
  const [scope, setScope] = useState<'all' | 'evaluate'>('evaluate')
  const [run, setRun] = useState<AgentRun | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [starting, setStarting] = useState(false)
  const alive = useRef(true)
  useEffect(() => () => { alive.current = false }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const value = await client.agentStatus()
      if (alive.current) { setStatus(value); setStatusError(null) }
    } catch (err) {
      if (alive.current) setStatusError(errorText(err))
    }
  }, [])

  const connected = ws.connection.status === 'connected'
  useEffect(() => { if (connected) void refreshStatus() }, [connected, refreshStatus])

  const runId = run?.run_id ?? null
  const running = isRunning(run)
  useEffect(() => {
    if (!runId || !running) return
    const timer = window.setInterval(async () => {
      try {
        const next = await client.agentRun(runId)
        if (!alive.current) return
        setRun(next)
        if (next.status !== 'running') void refreshStatus()
      } catch (err) {
        if (alive.current) setError(errorText(err))
      }
    }, 1000)
    return () => window.clearInterval(timer)
  }, [runId, running, refreshStatus])

  if (!connected || !ws.scenario) return null
  const head = ws.scenario
  const view = availability(status, statusError)
  const invalid = goalError(goal)
  const blocked = !view.available || running || starting || ws.draftDirty || ws.busy !== null

  const start = async () => {
    if (blocked || invalid) return
    setStarting(true)
    setError(null)
    try {
      const started = await client.startAgentRun({
        scenario_ref: { scenario_id: head.scenario_id, revision: head.revision, scope: head.scope },
        goal: goal.trim(),
        operations: scope === 'evaluate' ? ['evaluate_layout'] : null,
      })
      if (alive.current) setRun(started)
    } catch (err) {
      if (alive.current) { setError(errorText(err)); void refreshStatus() }
    } finally {
      if (alive.current) setStarting(false)
    }
  }
  const stop = async () => {
    if (!runId) return
    try { setRun(await client.stopAgentRun(runId)) } catch (err) { setError(errorText(err)) }
  }

  return (
    <div className="detail-section" data-testid="agent">
      <span className="section-kicker">PLANNING AGENT</span>
      <div className={`job-status tone-${view.tone}`} data-testid="agent-availability">
        <strong>{view.title}</strong>
        <span>{view.detail}</span>
      </div>
      <form className="proposal-form" onSubmit={e => { e.preventDefault(); void start() }}>
        <input aria-label="Goal for the planning agent" maxLength={MAX_GOAL} value={goal} disabled={running} onChange={e => setGoal(e.target.value)} className="agent-goal" />
        <label className="select-field agent-goal">
          TOOLS
          <select value={scope} disabled={running} onChange={e => setScope(e.target.value as 'all' | 'evaluate')}>
            <option value="evaluate">Evaluate only (most reliable)</option>
            <option value="all">All server tools{status ? ` (${status.allowed_operations.length})` : ''}</option>
          </select>
        </label>
        <button type="submit" className="secondary-action" disabled={blocked || Boolean(invalid)}>
          {starting ? 'Starting…' : `Ask the agent (accepted rev ${head.revision})`}
        </button>
      </form>
      {invalid && goal.length > 0 && <p className="fine-print text-warning">{invalid}</p>}
      {view.available && ws.draftDirty && <p className="fine-print">Accept or discard your draft first; the agent works on the accepted revision.</p>}
      <p className="fine-print">The agent runs on the server with the tools listed above. It can compute and explain, never accept: decisions stay with you.</p>
      <div role="status" aria-live="polite">
        {run && <AgentRunView run={run} />}
      </div>
      {running && (
        <button type="button" className="secondary-action" disabled={run?.stop_requested} onClick={() => void stop()}>
          {run?.stop_requested ? 'Stop requested' : 'Stop agent'}
        </button>
      )}
      {run && !running && run.computed_run_ids.length > 0 && (
        <p className="fine-print">
          <button type="button" className="text-action" disabled={ws.draftDirty} onClick={ws.reload}>Show agent results in the studio</button>
          {ws.draftDirty ? ' (accept or discard your draft first)' : ''}
        </p>
      )}
      {error && <p className="error-box" role="alert">{error}</p>}
    </div>
  )
}

function AgentRunView({ run }: { run: AgentRun }) {
  const view = runView(run)
  const uncited = uncitedRuns(run)
  return (
    <div data-testid="agent-run">
      <div className={`job-status tone-${view.tone}`} data-testid="agent-run-status">
        <strong>{view.title}</strong>
        <span>{view.detail}</span>
        <span>Run {short(run.run_id, 8)} · {run.model} · {run.model_completions} model turn{run.model_completions === 1 ? '' : 's'}{run.format_repairs_used ? ` · ${run.format_repairs_used} format repair` : ''}{run.elapsed_s !== null ? ` · ${run.elapsed_s.toFixed(1)} s` : ''}</span>
      </div>
      {run.tool_calls.length > 0 && (
        <table className="layout-table" data-testid="agent-tools">
          <caption className="sr-only">Tool calls the model chose, as executed by the backend</caption>
          <thead><tr><th scope="col">Tool</th><th scope="col">Backend outcome</th></tr></thead>
          <tbody>
            {run.tool_calls.map(call => (
              <tr key={call.tool_call_id}>
                <th scope="row">{call.index + 1}. {call.operation}<small title={call.arguments}>{call.arguments.length > 60 ? `${call.arguments.slice(0, 60)}…` : call.arguments}</small></th>
                <td>
                  {call.executed
                    ? <><span className={call.job_status === 'completed' ? 'text-ok' : 'text-warning'}>{call.job_status ?? 'answered'}</span>{call.run_id && <small title={call.run_id}>run {short(call.run_id)}</small>}{call.analytical_outcome && <small>{call.analytical_outcome.replace(/_/g, ' ')}</small>}</>
                    : <span className="text-warning">not executed</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {run.authoritative_summary && (
        <>
          <div className="currentness tone-success" data-testid="agent-evidence">
            <strong>BACKEND EVIDENCE · VERIFIED {run.evidence_verified ? 'YES' : 'NO'}</strong>
            <span>Cited: {run.cited_run_ids.map(id => short(id)).join(', ') || 'none'}</span>
          </div>
          <details className="evidence-details" data-testid="agent-summary">
            <summary>Summary generated from the stored results ({run.authoritative_summary.split('\n').length} lines)</summary>
            <ul>{run.authoritative_summary.split('\n').map((line, i) => <li key={i}>{line}</li>)}</ul>
          </details>
        </>
      )}
      {run.untrusted_model_narrative && (
        <div className="draft-box" data-testid="agent-model-text">
          <strong>Model explanation <span className="tag tag-warning">UNTRUSTED MODEL TEXT</span></strong>
          <p className="fine-print">{run.untrusted_model_narrative}</p>
          <p className="fine-print">Interpretation only. It can be wrong; the numbers above come from the backend.</p>
        </div>
      )}
      {uncited.length > 0 && (
        <p className="fine-print" data-testid="agent-uncited">Computed but not cited by an accepted answer: {uncited.map(id => short(id)).join(', ')}. These are real stored runs; open them from the studio.</p>
      )}
      {run.rejected_model_reply && (
        <details className="evidence-details">
          <summary>Rejected model reply (untrusted, diagnostic)</summary>
          <p className="fine-print">{run.rejected_model_reply}</p>
        </details>
      )}
    </div>
  )
}
