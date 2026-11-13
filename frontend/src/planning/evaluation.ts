import type { Job, JobRequest, Layout, Metric, Result, Scenario, ScenarioInput_Input, ScenarioRef, Vec3 } from '../api/types'

/**
 * Whether a stored Result may be presented as the answer for what the user is looking at.
 * Order matters: an older revision is superseded even if the user also has draft edits.
 */
export type Currentness =
  | 'current' // head revision, backend-selected run, no unsaved edits
  | 'stale-draft' // head revision and selected, but the draft has unsaved edits
  | 'not-selected' // head revision, but the backend's current selection is another run (or none)
  | 'superseded' // computed for an older scenario revision

export interface CurrentnessInput {
  readonly result: Pick<Result, 'run_id' | 'scenario_id' | 'scenario_revision' | 'scope'>
  readonly head: Pick<ScenarioRef, 'scenario_id' | 'revision' | 'scope'>
  /** run_id of `selections(head).evaluation.current_job`, or null when the backend has none. */
  readonly currentRunId: string | null
  readonly draftDirty: boolean
}

export function classifyResult({ result, head, currentRunId, draftDirty }: CurrentnessInput): Currentness {
  if (result.scenario_id !== head.scenario_id || result.scope !== head.scope || result.scenario_revision !== head.revision) return 'superseded'
  if (currentRunId !== result.run_id) return 'not-selected'
  if (draftDirty) return 'stale-draft'
  return 'current'
}

export const CURRENTNESS_LABEL: Record<Currentness, { label: string; detail: string }> = {
  current: { label: 'CURRENT', detail: 'Computed for the accepted revision you are viewing, and selected by the backend.' },
  'stale-draft': { label: 'STALE · UNSAVED EDITS', detail: 'You have moved the tree since this run. The number describes the last evaluated position, not your draft.' },
  'not-selected': { label: 'NOT CURRENT', detail: 'The backend no longer selects this run for this revision (a newer run or a failure replaced it).' },
  superseded: { label: 'SUPERSEDED', detail: 'Computed for an older scenario revision. Kept for history; it cannot describe the current scenario.' },
}

export const EXECUTION_MODE_LABEL: Record<Result['provenance']['execution_mode'], string> = {
  live: 'Live computation',
  cached: 'Cached result (exact same inputs)',
  recorded: 'Recorded result, not recomputed',
  fixture: 'Fixture, not a computation',
}

const UNIT_LABEL: Record<Metric['unit'], string> = {
  m: 'm', m2: 'm²', h: 'h', m2_h: 'm²·h', weighted_m2_h: 'weighted m²·h', kWh: 'kWh', kWh_per_m2: 'kWh/m²', GBP_pence: 'GBP pence',
}

export const unitLabel = (unit: Metric['unit']) => UNIT_LABEL[unit] ?? unit

/** Exact value as returned, trimmed only of float noise beyond 6 significant decimals. */
export function formatValue(value: number): string {
  if (!Number.isFinite(value)) return String(value)
  return Number(value.toFixed(6)).toString()
}

export function formatPence(pence: number): string {
  const sign = pence < 0 ? '−' : ''
  const abs = Math.abs(pence)
  return `${sign}£${Math.floor(abs / 100).toLocaleString('en-GB')}.${String(abs % 100).padStart(2, '0')}`
}

/** The metric for the scenario's primary case, if the result contains one. */
export function primaryMetric(result: Result, primaryCaseId: string | null): Metric | null {
  const additional = result.metrics.filter(m => m.metric_id === 'additional_shade')
  return additional.find(m => m.case_id === primaryCaseId) ?? additional[0] ?? result.metrics[0] ?? null
}

export type JobTone = 'neutral' | 'progress' | 'success' | 'warning' | 'danger'

export function describeJob(job: Job): { label: string; tone: JobTone; detail: string } {
  const superseded = job.superseded_by_revision !== null ? ` Superseded by revision ${job.superseded_by_revision}.` : ''
  switch (job.status) {
    case 'queued':
      return { label: job.cancel_requested ? 'Cancelling…' : 'Queued', tone: 'progress', detail: `Waiting for the local worker.${superseded}` }
    case 'running': {
      const p = job.progress
      const progress = p ? ` ${p.phase}: ${p.completed}/${p.total} ${p.unit}.` : ''
      return { label: job.cancel_requested ? 'Cancelling…' : 'Running', tone: 'progress', detail: `Evaluating on the local worker.${progress}${superseded}` }
    }
    case 'completed':
      return { label: 'Completed', tone: 'success', detail: `Run ${job.run_id ?? '—'} stored.${superseded}` }
    case 'cancelled':
      return { label: 'Cancelled', tone: 'warning', detail: `No result was stored for this job.${superseded}` }
    case 'failed':
      return {
        label: 'Failed',
        tone: 'danger',
        detail: `${job.error ? `${job.error.code}: ${job.error.message}` : 'The job failed without a stored error.'} No result was stored.${superseded}`,
      }
  }
}

const EPS = 1e-9
export const samePosition = (a: Vec3, b: Vec3) => a.every((x, i) => Math.abs(x - b[i]) <= EPS)

/** Positions are stored to the millimetre to avoid float noise from dragging. */
export const roundPosition = (p: readonly number[]): Vec3 => [0, 1, 2].map(i => Math.round(p[i] * 1000) / 1000 + 0) as unknown as Vec3

export const EDIT_LIMIT_M = 50

export function clampPosition(p: readonly number[]): Vec3 {
  const c = (x: number) => Math.min(EDIT_LIMIT_M, Math.max(-EDIT_LIMIT_M, Number.isFinite(x) ? x : 0))
  return roundPosition([c(p[0]), c(p[1]), p[2]])
}

export function nudge(p: Vec3, east: number, north: number): Vec3 {
  return clampPosition([p[0] + east, p[1] + north, p[2]])
}

/** Renew the job deadline when it would expire within this margin. */
export const DEADLINE_MARGIN_MS = 10 * 60 * 1000
export const DEADLINE_RENEWAL_MS = 2 * 60 * 60 * 1000

export interface CommitPlan {
  readonly layout: Layout
  readonly input: ScenarioInput_Input
  readonly ifMatch: number
  readonly deadlineRenewedTo: string | null
}

const isoZ = (ms: number) => new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z')

/**
 * Build the next immutable layout revision and the scenario input that points at it.
 * Only the moved placement's position (and, if nearly expired, the job deadline) change.
 */
export function buildCommit(scenario: Scenario, layout: Layout, placementId: string, position: Vec3, nowMs: number): CommitPlan {
  const ref = scenario.input.proposed_layout_ref
  if (!ref || ref.layout_id !== layout.layout_id || ref.revision !== layout.revision) {
    throw new Error('Scenario does not point at the layout being edited')
  }
  if (!layout.placements.some(p => p.placement_id === placementId)) throw new Error(`Unknown placement ${placementId}`)
  const nextLayout: Layout = {
    ...layout,
    revision: layout.revision + 1,
    placements: layout.placements.map(p => (p.placement_id === placementId ? { ...p, position_enu_m: roundPosition(position) } : p)),
  }
  const deadline = Date.parse(scenario.input.search.deadline_utc)
  const renew = !(deadline - nowMs > DEADLINE_MARGIN_MS)
  const deadlineRenewedTo = renew ? isoZ(nowMs + DEADLINE_RENEWAL_MS) : null
  const input: ScenarioInput_Input = {
    ...(scenario.input as unknown as ScenarioInput_Input),
    proposed_layout_ref: { layout_id: nextLayout.layout_id, revision: nextLayout.revision },
    search: deadlineRenewedTo ? { ...scenario.input.search, deadline_utc: deadlineRenewedTo } : scenario.input.search,
  }
  return { layout: nextLayout, input, ifMatch: scenario.revision, deadlineRenewedTo }
}

export function evaluateRequest(scenario: Scenario, requestId: string): JobRequest {
  const layoutRef = scenario.input.proposed_layout_ref
  if (!layoutRef) throw new Error('Scenario has no proposed layout to evaluate')
  return {
    request_id: requestId,
    operation: 'evaluate_layout',
    scenario_ref: { scenario_id: scenario.scenario_id, revision: scenario.revision, scope: scenario.scope },
    arguments: { layout_ref: layoutRef },
  }
}

export const refOf = (s: Scenario): ScenarioRef => ({ scenario_id: s.scenario_id, revision: s.revision, scope: s.scope })
