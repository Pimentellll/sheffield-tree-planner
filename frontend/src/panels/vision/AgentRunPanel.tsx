import { useId, useLayoutEffect, useRef, useState, type FocusEvent } from 'react'
import { agentPanelState, evidenceChain, narrativeView, type EvidenceChain, type FigureStatus, type NarrativeView } from '../../planning/agentEvidence'
import { isTerminalPhase, validateQuestion, type AgentAvailability, type AgentRunPhase, type AgentRunView, type AgentToolStep } from '../../planning/agentRun'
import { useAgentRun, type AgentRunController } from '../../planning/useAgentRun'
import type { RunRecord, Workspace } from '../../planning/useWorkspace'
import './AgentRunPanel.css'

/**
 * Planning-agent panel (#74). Renders whatever `AgentRunController` reports and nothing else.
 *
 * Trust boundary: the model's narrative and the run snapshot are never a source of numbers. Every
 * figure in the "Backend evidence" part comes from a `ws.runs` record through `evidenceChain`; the
 * narrative is plain text under the interpretation label, with its figures listed by `narrativeView`.
 * There is no agent-run API on the backend yet (#73), so in this build the controller's transport
 * reports "not connected" and the panel says so; manual planning is unaffected.
 *
 * Scope: a request is about the accepted scenario only. No map selection is threaded into the hook
 * yet, so the panel never names a "selected" tree; a host that tracks a real selection passes it as
 * `useAgentRun(ws, transport, { selectedFeatureId })` and the run facts then show it.
 *
 * Lifetime: without a `controller` prop the panel owns its run state. Opening the scenario editor,
 * changing screen or reloading the page unmounts it, which stops polling without cancelling the run
 * on the server. The hook keeps the request id and run id of an unfinished run in session storage,
 * so when the panel is mounted again the run is shown as "status unknown" and asked for again from
 * the server; a second run cannot be started until that one is re-checked or cleared. LIMIT: nothing
 * is polled while the panel is unmounted, and a run that ended is not kept across a reload. A host
 * that wants continuous polling calls `useAgentRun` where the studio stays mounted (App level) and
 * passes the result as `controller` (through `AgentPanel`). With the default unavailable transport
 * no run can exist, so none of this has an effect in the current build.
 */
export function AgentRunPanel({ ws, controller, headingId }: { ws: Workspace; controller?: AgentRunController; headingId?: string }) {
  return controller
    ? <AgentRunView ws={ws} c={controller} headingId={headingId} />
    : <AgentRunWithHook ws={ws} headingId={headingId} />
}

function AgentRunWithHook({ ws, headingId }: { ws: Workspace; headingId?: string }) {
  // Default transport only (unavailable). See the lifetime limit above.
  const c = useAgentRun(ws)
  return <AgentRunView ws={ws} c={c} headingId={headingId} />
}

// ---------------------------------------------------------------------------------------------
// Words

const PHASE_WORD: Record<AgentRunPhase, string> = {
  submitting: 'Submitting',
  running: 'Running',
  stop_requested: 'Stop requested',
  completed: 'Completed',
  stopped: 'Stopped',
  failed: 'Failed',
  status_unknown: 'Status unknown',
}

function phaseDetail(run: AgentRunView): string {
  switch (run.phase) {
    case 'submitting': return 'Sending the request to the backend. It has not answered yet.'
    case 'running': return 'The backend reports the run is in progress. Tool steps appear below as the backend reports them.'
    case 'stop_requested': return 'Stop requested. Waiting for the backend to report that the run has ended.'
    case 'completed': return `The backend reports the run has ended${run.outcome ? ` with outcome "${run.outcome}"` : ''}.`
    case 'stopped': return `The backend reports the run was stopped${run.outcome ? ` (outcome "${run.outcome}")` : ''}.`
    case 'failed': return `The backend reports the run failed${run.error ? `: ${run.error}` : '.'}`
    case 'status_unknown':
      return `The ${run.agentRunId ? 'last ' : ''}request may or may not have reached the backend, so the run's actual status is unknown. ${run.agentRunId
        ? 'Re-check asks the backend for this run\'s status again.'
        : 'Re-check sends the same request again under the same request id; the backend is expected to treat it as the same run, but this panel cannot confirm that.'}${run.error ? ` Last error: ${run.error}` : ''}`
  }
}

const PHASE_TONE: Record<AgentRunPhase, string> = {
  submitting: 'progress', running: 'progress', stop_requested: 'progress',
  completed: 'ok', stopped: 'muted', failed: 'warn', status_unknown: 'warn',
}

const STEP_WORD: Record<AgentToolStep['status'], string> = {
  requested: 'requested', running: 'running', completed: 'completed', failed: 'failed',
}

// Avoids claiming a check the guard does not make: "appears" means the value occurs somewhere in a
// loaded computed result, not that the model attached it to the right case or layout.
const FIGURE_WORD: Record<FigureStatus, string> = {
  unsupported: 'unsupported: no registered operation computes this',
  unverified: 'not found in a computed result loaded here',
  'appears-in-result': 'appears in a computed result (still model text)',
}

function availabilityWord(a: AgentAvailability | null): { pill: string; tone: string } {
  if (!a) return { pill: 'CHECKING', tone: 'muted' }
  return a.kind === 'available' ? { pill: 'AVAILABLE', tone: 'ok' } : { pill: 'NOT CONNECTED', tone: 'muted' }
}

// ---------------------------------------------------------------------------------------------
// Evidence lookup (backend records only)

type StepEvidence =
  | { readonly kind: 'not-loaded' }
  | { readonly kind: 'chain'; readonly record: RunRecord; readonly chain: EvidenceChain }

function findRecord(runs: readonly RunRecord[], step: AgentToolStep): RunRecord | null {
  if (step.jobId) {
    const byJob = runs.find(r => r.job.job_id === step.jobId)
    if (byJob) return byJob
  }
  if (step.runId) return runs.find(r => r.result?.run_id === step.runId) ?? null
  return null
}

function stepEvidence(ws: Workspace, step: AgentToolStep): StepEvidence {
  const record = findRecord(ws.runs, step)
  if (!record?.result) return { kind: 'not-loaded' }
  const chain = evidenceChain(record.job, record.result, ws.currentness(record.result))
  // The step's ids must both agree with the matched record. A mismatch either way (the record was
  // found by job but names another run, or found by run but belongs to another job) is shown as a
  // problem, never as a clean chain, so figures are never attributed to an id that did not produce them.
  const mismatches: string[] = []
  if (step.jobId && record.job.job_id !== step.jobId) {
    mismatches.push(`The agent step names job ${step.jobId}, but the loaded result run ${record.result.run_id} belongs to job ${record.job.job_id}.`)
  }
  if (step.runId && record.result.run_id !== step.runId) {
    mismatches.push(`The agent step names run ${step.runId}, but the loaded result for job ${record.job.job_id} is run ${record.result.run_id}.`)
  }
  if (mismatches.length) {
    return { kind: 'chain', record, chain: { ok: false, problems: [...mismatches, ...(chain.ok ? [] : chain.problems)] } }
  }
  return { kind: 'chain', record, chain }
}

const idLoaded = (runs: readonly RunRecord[], id: string) =>
  runs.some(r => r.result !== null && (r.job.job_id === id || r.result.run_id === id))

// ---------------------------------------------------------------------------------------------
// View

function AgentRunView({ ws, c, headingId }: { ws: Workspace; c: AgentRunController; headingId?: string }) {
  const uid = useId()
  const titleId = headingId ?? `${uid}-title`
  const inputId = `${uid}-input`
  const hintId = `${uid}-hint`
  const errorId = `${uid}-error`
  const blockedId = `${uid}-blocked`
  const statusId = `${uid}-status`

  const [text, setText] = useState('')
  const [validation, setValidation] = useState<string | null>(null)

  const rootRef = useRef<HTMLDivElement>(null)
  const statusRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  // Focus keeping: when a focused control inside the panel is removed or disabled by a status change
  // (Stop after the run ends, Re-check after it resolves), focus moves to the status line instead of
  // falling back to the page. A deliberate move elsewhere clears the flag.
  const focusInside = useRef(false)

  useLayoutEffect(() => {
    const root = rootRef.current
    if (!root || !focusInside.current) return
    const active = document.activeElement
    const lost = !active || active === document.body || (root.contains(active) && active instanceof HTMLButtonElement && active.disabled)
    if (lost) statusRef.current?.focus()
  })

  const onFocusIn = () => { focusInside.current = true }
  const onFocusOut = (e: FocusEvent<HTMLDivElement>) => {
    const target = e.target as HTMLElement
    const next = e.relatedTarget as Node | null
    if (next && rootRef.current?.contains(next)) return
    // A control removed from the page (or just disabled) is not a deliberate move away.
    setTimeout(() => {
      if (target.isConnected && !(target instanceof HTMLButtonElement && target.disabled)) focusInside.current = false
    }, 0)
  }

  const availability = c.availability
  const available = availability?.kind === 'available'
  const health = ws.connection.status === 'connected' ? ws.connection.health : null
  const manual = agentPanelState(health)
  const run = c.run
  const terminal = run ? isTerminalPhase(run.phase) : false
  const word = availabilityWord(availability)

  const submit = () => {
    const v = validateQuestion(text)
    if (!v.ok) { setValidation(v.reason); inputRef.current?.focus(); return }
    setValidation(null)
    if (!c.canSubmit) return
    c.submit(v.question)
  }

  const stop = () => { c.stop(); statusRef.current?.focus() }
  const recheck = () => { c.recheck(); statusRef.current?.focus() }
  const clear = () => { c.clear(); inputRef.current?.focus() }

  // The status line already gives the reason while the agent is unavailable or being checked, so the
  // blocked line appears only for reasons the status line does not state (no scenario, draft edits),
  // and not while a run is in progress or unknown (its phase line says why).
  const showBlocked = available && !c.canSubmit && c.blockedReason !== null && (!run || terminal)
  const describedBy = (available
    ? [ws.scenario ? hintId : null, validation ? errorId : null, showBlocked ? blockedId : null]
    : [statusId]
  ).filter(Boolean).join(' ') || undefined
  const manualLine = !health
    ? 'Manual planning (evaluate, search, compare, export) does not need the agent: start the local backend to use it.'
    : manual.manualEvaluateAvailable
      ? `Manual planning (evaluate, search, compare, export) is unaffected.${manual.workerRunning === false ? ' The job worker is in manual mode, so a submitted evaluation waits until a worker is run.' : ''}`
      : 'Manual planning (search, compare, export) is unaffected; this backend offers no evaluate_layout operation.'

  // Figures in the narrative are checked against computed results the agent's steps link to, and
  // only those whose job → result linkage holds.
  const linked = run
    ? run.steps.map(s => stepEvidence(ws, s)).flatMap(e => (e.kind === 'chain' && e.chain.ok && e.record.result ? [e.record.result] : []))
    : []
  const narrative: NarrativeView | null = run?.narrative
    ? narrativeView(run.narrative, linked.length ? { metrics: linked.flatMap(r => r.metrics), layouts: linked.flatMap(r => r.layouts) } : null)
    : null
  const evidenceSteps = run ? run.steps.filter(s => s.jobId || s.runId) : []

  return (
    <div className="arp-root" data-testid="arp-root" ref={rootRef} onFocus={onFocusIn} onBlur={onFocusOut}>
      <div className="agent-head arp-head">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z" /></svg>
        <h2 id={titleId}>Planning agent</h2>
        <span className={`status-pill sp-${word.tone}`} data-testid="arp-availability"><i aria-hidden="true" />{word.pill}</span>
        {availability?.kind === 'available' && availability.model && <span className="caption mono arp-model">model {availability.model}</span>}
      </div>

      {/* One polite live region: availability while there is no run, otherwise the run's phase in words. */}
      <div id={statusId} className="arp-status" role="status" aria-live="polite" tabIndex={-1} ref={statusRef} data-testid="arp-status" data-phase={run?.phase ?? 'none'}>
        {run ? (
          <>
            <p className="arp-status-line"><span className={`status-pill sp-${PHASE_TONE[run.phase]}`}><i aria-hidden="true" />{PHASE_WORD[run.phase].toUpperCase()}</span> <span>{phaseDetail(run)}</span></p>
          </>
        ) : !availability ? (
          <p className="arp-status-line">Checking whether a planning agent is connected…</p>
        ) : availability.kind === 'unavailable' ? (
          <p className="arp-status-line">{availability.reason}</p>
        ) : (
          <p className="arp-status-line">Planning agent available{availability.model ? ` (model ${availability.model})` : ''}. Its answers are model text; figures come only from computed results.</p>
        )}
      </div>

      <p className="caption arp-manual">{manualLine}</p>
      <p className="caption mono arp-ops" data-testid="backend-operations">Backend operations: {health ? (health.available_operations.join(', ') || 'none') : 'unknown while offline'}</p>

      {/* While the agent is unavailable (or being checked) the form collapses to one disabled row: the
          status line above already says why, so nothing here repeats it. */}
      <form className={`arp-form${available ? '' : ' arp-form-off'}`} onSubmit={e => { e.preventDefault(); submit() }} noValidate>
        <label htmlFor={inputId} className={available ? 'arp-label' : 'sr-only'}>Request for the planning agent</label>
        {/* The request carries the accepted scenario key only (no map selection is sent), so that is all the hint names. */}
        {available && ws.scenario && (
          <p id={hintId} className="caption arp-hint" data-testid="arp-hint">About the accepted scenario, revision {ws.scenario.revision}.</p>
        )}
        <textarea
          id={inputId}
          ref={inputRef}
          className="arp-input"
          data-testid="arp-input"
          rows={available ? 2 : 1}
          value={text}
          disabled={!available}
          placeholder={available ? 'For example: evaluate the proposed planting layout' : undefined}
          aria-invalid={validation ? true : undefined}
          aria-describedby={describedBy}
          onChange={e => { setText(e.target.value); if (validation) setValidation(null) }}
        />
        {validation && <p id={errorId} className="caption text-warning arp-validation" data-testid="arp-validation">{validation}</p>}
        <div className="arp-actions">
          <button type="submit" className="arp-button arp-primary" data-testid="arp-submit" disabled={!c.canSubmit}>Start</button>
          {run?.phase === 'running' && <button type="button" className="arp-button" data-testid="arp-stop" onClick={stop}>Stop</button>}
          {run?.phase === 'status_unknown' && <button type="button" className="arp-button" data-testid="arp-recheck" onClick={recheck}>Re-check status</button>}
          {run && (terminal || run.phase === 'status_unknown') && <button type="button" className="arp-button" data-testid="arp-clear" onClick={clear}>Clear</button>}
        </div>
        {showBlocked && <p id={blockedId} className="caption arp-blocked" data-testid="arp-blocked">{c.blockedReason}</p>}
      </form>

      {run && (
        <div className="arp-details" role="group" aria-label="Agent run details" tabIndex={0}>
          {c.headMoved && (
            <p className="arp-note arp-head-moved" data-testid="arp-head-moved">
              <strong>Older revision.</strong> This answer describes accepted revision {run.scenario.revision}. The accepted scenario is now {ws.scenario ? `revision ${ws.scenario.revision}` : 'a later revision'}, so the answer is kept for reference and is not current.
            </p>
          )}

          <dl className="arp-facts">
            <div><dt>Request</dt><dd className="mono">{run.requestId}</dd></div>
            <div><dt>Agent run</dt><dd className="mono">{run.agentRunId ?? 'not assigned by the backend yet'}</dd></div>
            <div><dt>Scenario</dt><dd className="mono">{run.scenario.scope} {run.scenario.scenario_id} revision {run.scenario.revision}</dd></div>
            {run.selectedFeatureId && <div><dt>Selected</dt><dd className="mono">{run.selectedFeatureId}</dd></div>}
            <div><dt>Question</dt><dd className="arp-question">{run.question}</dd></div>
          </dl>

          <h3 className="arp-subhead">Tool steps</h3>
          {run.steps.length ? (
            <ol className="arp-steps" data-testid="arp-steps">
              {run.steps.map(s => (
                <li key={s.seq} className={`arp-step arp-step-${s.status}`}>
                  <span className="mono arp-tool">{s.tool}</span> <span className="arp-step-status">{STEP_WORD[s.status]}</span>
                  {(s.jobId || s.runId) && (
                    <span className="caption mono arp-ids">{s.jobId && <>job {s.jobId}</>}{s.jobId && s.runId && ' · '}{s.runId && <>run {s.runId}</>}</span>
                  )}
                  {s.status === 'failed' && s.error && <span className="caption text-warning arp-step-error">Error: {s.error}</span>}
                </li>
              ))}
            </ol>
          ) : (
            <p className="caption" data-testid="arp-steps">No tool steps reported by the backend.</p>
          )}

          <section className="arp-evidence" data-testid="arp-evidence" aria-label="Backend evidence">
            <h3 className="arp-subhead">Backend evidence (computed)</h3>
            {evidenceSteps.length === 0 && <p className="caption">No step names a job or result, so there is no computed evidence to show.</p>}
            {evidenceSteps.map(s => {
              const e = stepEvidence(ws, s)
              const ids = `${s.jobId ? `job ${s.jobId}` : ''}${s.jobId && s.runId ? ' · ' : ''}${s.runId ? `run ${s.runId}` : ''}`
              if (e.kind === 'not-loaded') {
                return (
                  <div key={s.seq} className="arp-ev">
                    <p className="caption"><span className="mono">{s.tool}</span> · <span className="mono">{ids}</span></p>
                    <p className="caption">Result not loaded in this workspace.</p>
                  </div>
                )
              }
              return (
                <details key={s.seq} className="arp-ev">
                  <summary><span className="mono">{s.tool}</span> · <span className="mono">{ids}</span>{e.chain.ok ? '' : ' · cannot be shown'}</summary>
                  {e.chain.ok
                    ? <dl className="arp-chain">{e.chain.steps.map((st, i) => <div key={`${st.kind}-${i}`}><dt>{st.label}</dt><dd className={st.kind === 'limitation' || st.kind === 'missing-metric' ? 'text-warning' : undefined}>{st.value}</dd></div>)}</dl>
                    : <ul className="text-warning arp-problems">{e.chain.problems.map(p => <li key={p}>{p}</li>)}</ul>}
                </details>
              )
            })}
          </section>

          {narrative && (
            <section className="arp-narrative" data-testid="arp-narrative" aria-label={narrative.label}>
              <h3 className="arp-subhead">{narrative.label}</h3>
              {narrative.needsWarning && (
                <p className="arp-note" data-testid="arp-narrative-warning">
                  <strong>Check before relying on this.</strong> The text states figures that do not appear in a computed result loaded here{narrative.temperatureMentioned ? ', or a temperature, which no registered operation computes' : ''}. Use the backend evidence above for numbers.
                </p>
              )}
              {/* Plain text only: React escapes it; no HTML from the model is rendered. */}
              <p className="arp-narrative-text">{narrative.text}</p>
              {narrative.figures.length > 0 && (
                <>
                  <h4 className="arp-minorhead">Figures in the model text</h4>
                  <ul className="arp-figures">
                    {narrative.figures.map(f => <li key={`${f.index}-${f.text}`} data-status={f.status}><span className="mono">{f.text}</span>: {FIGURE_WORD[f.status]}{f.contextOnly ? ' (a count, for context)' : ''}</li>)}
                  </ul>
                </>
              )}
            </section>
          )}

          {run.evidenceIds.length > 0 && (
            <section className="arp-cited" aria-label="Ids the model cited">
              <h4 className="arp-minorhead">Ids the model cited</h4>
              <ul className="arp-figures">
                {run.evidenceIds.map(id => <li key={id}><span className="mono">{id}</span>: {idLoaded(ws.runs, id) ? 'matched a loaded result' : 'not found here'}</li>)}
              </ul>
            </section>
          )}
        </div>
      )}
    </div>
  )
}
