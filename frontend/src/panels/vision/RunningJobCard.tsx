import { CANCEL_NOTE, runningJobView, supersededView } from '../../planning/runningJob'
import { latestEvaluation } from '../../planning/shell'
import type { Workspace } from '../../planning/useWorkspace'
import './RunningJobCard.css'

const short = (value: string, n = 8) => (value.length > n + 1 ? `${value.slice(0, n)}…` : value)

/** A shortened id on screen with the full value for screen readers, as the context header writes ids. */
function Id({ value, n }: { value: string; n?: number }) {
  return <><span aria-hidden="true">{short(value, n)}</span><span className="sr-only">{value}</span></>
}

/**
 * C03: the running-job card for the right panel. Shows only what the Job API reports: status,
 * operation, the job's own scenario revision, identity and real progress counts (or an
 * indeterminate indicator). No phase list, percentage, elapsed clock or ETA is shown.
 */
export function RunningJobCard({ ws }: { ws: Workspace }) {
  const v = runningJobView(ws.activeJob, ws.jobStatusLost)
  if (!v) return null
  const showCancel = v.status === 'queued' || v.status === 'running'
  return (
    <section className="detail-section rjc-card" aria-labelledby="rjc-heading" data-testid="rjc-card">
      <span className="section-kicker">{v.kicker}</span>
      <h3 id="rjc-heading" className="section-title">{v.heading}</h3>

      {/* Only the status changes are announced; the re-check sits with its explanation, as in the evaluation panel. */}
      <div className="rjc-status" role="status" aria-live="polite">
        <span className={`status-pill sp-${v.pillTone}`} data-testid="rjc-status"><i aria-hidden="true" />{v.statusWord.toUpperCase()}</span>
        <p className="fine-print">{v.detail}</p>
        {v.canRecheck && (
          <button type="button" className="secondary-action" onClick={() => void ws.recheckJob()}>Re-check job status</button>
        )}
      </div>

      {v.progress.kind === 'counts' && (
        <div className="rjc-progress">
          <progress max={v.progress.total} value={v.progress.completed} aria-label="Job progress" />
          <span className="mono caption">{v.progress.completed} / {v.progress.total}</span>
        </div>
      )}
      {v.progress.kind === 'indeterminate' && (
        <div className="rjc-progress">
          <progress aria-label="Job in progress; the backend reports no progress counts" data-testid="rjc-indeterminate" />
          <span className="caption">{v.progress.caption}</span>
        </div>
      )}

      <div className="rjc-facts">
        <div className="readiness-row"><span>Job</span><strong className="mono"><Id value={v.jobId} /> · slot {v.viewSlot} · seq {v.selectionSeq}</strong></div>
        <div className="readiness-row"><span>Scenario</span><strong className="mono"><Id value={v.scenarioId} /> · rev {v.scenarioRevision} · {v.scope}</strong></div>
        <div className="readiness-row"><span>Fingerprint</span><strong className="mono"><Id value={v.fingerprint} n={12} /></strong></div>
      </div>

      {showCancel && (
        <div className="rjc-actions">
          <button type="button" className="secondary-action" disabled={!v.canCancel || ws.busy === 'cancelling'} onClick={() => void ws.cancel()}>
            {v.cancelLabel}
          </button>
          <span className="caption">{CANCEL_NOTE}</span>
        </div>
      )}
    </section>
  )
}

/**
 * C03: the banner for an older result that a newer accepted revision has superseded. Whether it
 * is superseded comes from the workspace's own currentness rule, so it agrees with the result
 * card; it states by which revision when known and never repeats the old metric value.
 */
export function SupersededResultBanner({ ws }: { ws: Workspace }) {
  const record = latestEvaluation(ws.runs, ws.currentRunIds.evaluation)
  const isSuperseded = record?.result ? ws.currentness(record.result) === 'superseded' : false
  const v = supersededView(record?.job ?? null, ws.scenario, isSuperseded)
  if (!v) return null
  return (
    <div className="rjc-superseded glass-light" role="status" data-testid="rjc-superseded">
      <div className="rjc-superseded-head">
        {/* The strike-through is decoration; the word SUPERSEDED carries the meaning. */}
        <span className="status-pill sp-muted"><i aria-hidden="true" /><span className="rjc-strike">{v.pill}</span></span>
        <span className="caption mono">{v.meta}</span>
      </div>
      <p>{v.body}</p>
    </div>
  )
}
