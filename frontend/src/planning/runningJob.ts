import type { Job, ScenarioRef } from '../api/types'
import { CURRENTNESS_LABEL, describeJob, progressView, type ProgressView } from './evaluation'

/**
 * View logic for the Vision v2 C03 running-job card and superseded-result banner.
 *
 * Only what the Job API actually reports is shown: status, operation, job id, the job's own
 * scenario revision, slot/sequence and input fingerprint. Progress comes from `progressView`
 * (counts only when the backend reports total > 0, otherwise an indeterminate indicator). The
 * design's phase list, percentage, per-phase durations, elapsed clock, deadline and budget have
 * no source on Job today and are deliberately absent.
 */

export type RunningJobStatus = Job['status'] | 'status-unknown'

/** The status words, exactly. No "succeeded". */
export const STATUS_WORD: Record<RunningJobStatus, string> = {
  queued: 'Queued',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
  cancelled: 'Cancelled',
  'status-unknown': 'Status unknown',
}

/** Shared `.status-pill` tone suffix (`sp-<tone>` in styles.css). The word, not the colour, carries the state. */
export type PillTone = 'progress' | 'ok' | 'warn' | 'muted'

// Same tones as describeJob (evaluation.ts): cancelled and failed are warnings, not muted.
const PILL_TONE: Record<RunningJobStatus, PillTone> = {
  queued: 'progress', running: 'progress', completed: 'ok', failed: 'warn', cancelled: 'warn', 'status-unknown': 'warn',
}

/** Section kicker per operation, an uppercase word like every other kicker (shell.ts uses the same words). */
const KICKER: Record<Job['operation'], string> = {
  evaluate_layout: 'EVALUATION', search_layouts: 'SEARCH', compare_locations: 'COMPARISON', compare_scenarios: 'COMPARISON',
}

const VERB: Record<Job['operation'], string> = {
  evaluate_layout: 'Evaluating', search_layouts: 'Searching', compare_locations: 'Comparing locations for', compare_scenarios: 'Comparing scenarios for',
}

const NOUN: Record<Job['operation'], string> = {
  evaluate_layout: 'evaluation', search_layouts: 'search', compare_locations: 'comparison', compare_scenarios: 'comparison',
}

const capitalise = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/** Same wording as the evaluation panel's "status unknown" state (Panels.tsx), so both say one thing. */
export const STATUS_LOST_DETAIL = 'Contact was lost while following this job. It may still be running on the backend; no result is assumed.'
export const CANCEL_NOTE = 'Cancelling keeps no partial result.'

export interface RunningJobView {
  readonly status: RunningJobStatus
  readonly statusWord: string
  readonly pillTone: PillTone
  readonly operation: Job['operation']
  /** Uppercase section kicker: EVALUATION, SEARCH or COMPARISON. */
  readonly kicker: string
  /** "Searching revision 4" while active; "Search of revision 4" once finished or unknown. The job's OWN revision. */
  readonly heading: string
  readonly jobId: string
  readonly scenarioId: string
  readonly scenarioRevision: number
  readonly scope: Job['scope']
  readonly viewSlot: Job['view_slot']
  readonly selectionSeq: number
  /** Full input fingerprint; the component shortens it the way ResultCard does. */
  readonly fingerprint: string
  readonly detail: string
  readonly progress: ProgressView
  readonly cancelRequested: boolean
  /** Offer cancel: the job is queued or running, its status is known, and no cancel is pending. */
  readonly canCancel: boolean
  readonly cancelLabel: string
  /** Offer "Re-check job status": only when the status is unknown. */
  readonly canRecheck: boolean
}

const active = (status: Job['status']) => status === 'queued' || status === 'running'

/**
 * The card's content for a job, or null when there is no job. `statusLost` (Workspace.jobStatusLost)
 * only applies while the job was last seen queued or running: it is then shown as "Status unknown",
 * never as running, with no progress indicator.
 */
export function runningJobView(job: Job | null, statusLost: boolean): RunningJobView | null {
  if (!job) return null
  const lost = statusLost && active(job.status)
  const status: RunningJobStatus = lost ? 'status-unknown' : job.status
  const superseded = job.superseded_by_revision !== null ? ` Superseded by revision ${job.superseded_by_revision}.` : ''
  // describeJob's running detail can include the backend's phase name; the card never shows phases.
  const detail = lost
    ? STATUS_LOST_DETAIL
    : job.status === 'queued' ? `Waiting for the local worker.${superseded}`
      : job.status === 'running' ? `The local worker is processing this ${NOUN[job.operation]}.${superseded}`
        : describeJob(job).detail
  const working = active(job.status) && !lost
  return {
    status,
    statusWord: STATUS_WORD[status],
    pillTone: PILL_TONE[status],
    operation: job.operation,
    kicker: KICKER[job.operation],
    heading: working ? `${VERB[job.operation]} revision ${job.scenario_revision}` : `${capitalise(NOUN[job.operation])} of revision ${job.scenario_revision}`,
    jobId: job.job_id,
    scenarioId: job.scenario_id,
    scenarioRevision: job.scenario_revision,
    scope: job.scope,
    viewSlot: job.view_slot,
    selectionSeq: job.selection_seq,
    fingerprint: job.input_fingerprint,
    detail,
    progress: lost ? { kind: 'none' } : progressView(job),
    cancelRequested: job.cancel_requested,
    canCancel: working && !job.cancel_requested,
    cancelLabel: job.cancel_requested ? 'Cancel requested' : `Cancel ${NOUN[job.operation]}`,
    canRecheck: lost,
  }
}

export interface SupersededView {
  /** Revision the older result was computed for. */
  readonly revision: number
  /** Revision that superseded it, when known: the backend's Job.superseded_by_revision, else a newer accepted head. */
  readonly supersededBy: number | null
  readonly source: 'job' | 'head' | null
  readonly runId: string | null
  readonly pill: string
  readonly meta: string
  readonly body: string
}

/**
 * The banner for an older result's job, or null. Whether the result IS superseded is not decided
 * here: the caller passes the project's own rule (`ws.currentness(result) === 'superseded'`, from
 * evaluation.ts `classifyResult`), so the banner and the result card never disagree. This only
 * says by which revision, preferring the backend's `superseded_by_revision`, and never carries a
 * metric value.
 */
export function supersededView(
  job: Pick<Job, 'scenario_id' | 'scope' | 'scenario_revision' | 'superseded_by_revision' | 'run_id'> | null,
  head: Pick<ScenarioRef, 'scenario_id' | 'revision' | 'scope'> | null,
  isSuperseded: boolean,
): SupersededView | null {
  if (!job || !isSuperseded) return null
  const fromJob = job.superseded_by_revision
  // The head can only be named when it is the same scenario and scope (classifyResult also calls a
  // result from another scenario or scope superseded, but no revision of that scenario replaced it).
  const fromHead = head !== null && head.scenario_id === job.scenario_id && head.scope === job.scope && head.revision > job.scenario_revision
    ? head.revision
    : null
  const supersededBy = fromJob ?? fromHead
  const r = job.scenario_revision
  return {
    revision: r,
    supersededBy,
    source: fromJob !== null ? 'job' : fromHead !== null ? 'head' : null,
    runId: job.run_id,
    // Same words as the provenance strip (shell.ts provenanceStatus): REV N RUN · SUPERSEDED.
    pill: `REV ${r} RUN · SUPERSEDED`,
    meta: `${job.run_id ?? 'no run id'} · kept in history`,
    // The pill already names revision r; the body reuses the project's own superseded wording.
    body: `${CURRENTNESS_LABEL.superseded.detail}${supersededBy !== null ? ` Superseded by revision ${supersededBy}.` : ''}`,
  }
}
