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

/**
 * Pill tone. `progress`/`ok`/`warn`/`muted` are the shared `.sp-<tone>` classes; `danger` is the
 * shared `.tone-danger` class (styles.css has no `sp-danger`). The word, not the colour, carries the state.
 */
export type PillTone = 'progress' | 'ok' | 'warn' | 'muted' | 'danger'

/** The shared class for a pill tone. */
export const pillToneClass = (tone: PillTone) => (tone === 'danger' ? 'tone-danger' : `sp-${tone}`)

// Same tones as describeJob (evaluation.ts): failed is danger, cancelled and unknown are warnings.
const PILL_TONE: Record<RunningJobStatus, PillTone> = {
  queued: 'progress', running: 'progress', completed: 'ok', failed: 'danger', cancelled: 'warn', 'status-unknown': 'warn',
}

/** Pill word while a cancel is pending on a queued or running job, as describeJob labels it. */
export const CANCELLING_WORD = 'Cancelling…'

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
    statusWord: working && job.cancel_requested ? CANCELLING_WORD : STATUS_WORD[status],
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
  /** The backend's Job.superseded_by_revision only. Null when the job snapshot does not carry it. */
  readonly supersededBy: number | null
  /**
   * The newer accepted head of the same scenario and scope, stated as the current revision only.
   * It is NOT claimed as the superseder: ws.runs snapshots are written when polling ends and never
   * refreshed, so a result that completed before a newer revision was accepted carries
   * superseded_by_revision null, and the head may be several revisions past the one that
   * superseded it (rev 3 result, rev 4 accepted but failed, head at rev 6).
   */
  readonly acceptedRevision: number | null
  readonly runId: string | null
  readonly pill: string
  readonly meta: string
  readonly body: string
}

/**
 * The banner for an older result's job, or null. Whether the result IS superseded is not decided
 * here: the caller passes the project's own rule (`ws.currentness(result) === 'superseded'`, from
 * evaluation.ts `classifyResult`), so the banner and the result card never disagree. It names the
 * superseding revision only from the backend's `superseded_by_revision`; otherwise it states the
 * current accepted revision without claiming that revision superseded it. Never carries a metric value.
 */
export function supersededView(
  job: Pick<Job, 'scenario_id' | 'scope' | 'scenario_revision' | 'superseded_by_revision' | 'run_id'> | null,
  head: Pick<ScenarioRef, 'scenario_id' | 'revision' | 'scope'> | null,
  isSuperseded: boolean,
): SupersededView | null {
  if (!job || !isSuperseded) return null
  const supersededBy = job.superseded_by_revision
  // The head is only stated for the same scenario and scope (classifyResult also calls a result from
  // another scenario or scope superseded; that scenario's head says nothing about this result).
  const acceptedRevision = head !== null && head.scenario_id === job.scenario_id && head.scope === job.scope && head.revision > job.scenario_revision
    ? head.revision
    : null
  const r = job.scenario_revision
  const which = supersededBy !== null
    ? ` Superseded by revision ${supersededBy}.`
    : acceptedRevision !== null ? ` The accepted revision is now ${acceptedRevision}.` : ''
  return {
    revision: r,
    supersededBy,
    acceptedRevision,
    runId: job.run_id,
    // Same words as the provenance strip (shell.ts provenanceStatus): REV N RUN · SUPERSEDED.
    pill: `REV ${r} RUN · SUPERSEDED`,
    meta: `${job.run_id ?? 'no run id'} · kept in history`,
    // The pill already names revision r; the body reuses the project's own superseded wording.
    body: `${CURRENTNESS_LABEL.superseded.detail}${which}`,
  }
}
