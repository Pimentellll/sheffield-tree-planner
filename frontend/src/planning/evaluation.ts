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
  'stale-draft': { label: 'STALE · UNSAVED EDITS', detail: 'You have unaccepted edits (tree position or requirements) since this run. The number describes the accepted revision, not your draft.' },
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
      // Counts are shown only when the backend reports a positive total; "0/0" is no count at all.
      const progress = p && p.total > 0 ? ` ${p.phase}: ${p.completed}/${p.total} ${p.unit}.` : ''
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

/**
 * How the job's progress may be shown. Counts only when the backend reported a positive total;
 * otherwise an indeterminate indicator that says nothing is estimated. Nothing for a finished job.
 */
export type ProgressView =
  | { readonly kind: 'none' }
  | { readonly kind: 'counts'; readonly completed: number; readonly total: number }
  | { readonly kind: 'indeterminate'; readonly caption: string }

export const NO_PROGRESS_CAPTION = 'The backend reports no progress counts, so no percentage or phase is estimated.'

export function progressView(job: Pick<Job, 'status' | 'progress'>): ProgressView {
  if (job.status !== 'queued' && job.status !== 'running') return { kind: 'none' }
  const p = job.progress
  if (p && p.total > 0) return { kind: 'counts', completed: p.completed, total: p.total }
  return { kind: 'indeterminate', caption: NO_PROGRESS_CAPTION }
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

/** Human-editable hard requirements. Budget basis stays upfront integer GBP pence. */
export interface Requirements {
  readonly budgetPence: number
  readonly maxTreeCount: number | null
  readonly excludedRegionIds: readonly string[]
}

export function requirementsOf(scenario: Pick<Scenario, 'input'>): Requirements {
  const c = scenario.input.constraints
  return { budgetPence: c.budget_pence, maxTreeCount: c.max_tree_count, excludedRegionIds: [...c.excluded_region_ids].sort() }
}

export function sameRequirements(a: Requirements, b: Requirements): boolean {
  const ea = [...a.excludedRegionIds].sort()
  const eb = [...b.excludedRegionIds].sort()
  return a.budgetPence === b.budgetPence && a.maxTreeCount === b.maxTreeCount && ea.length === eb.length && ea.every((id, i) => id === eb[i])
}

export const MAX_BUDGET_PENCE = 100_000_000_00 // £100m: a sanity bound for the editor, not a policy

/** Parse "1234", "1234.5" or "£1,234.50" to integer pence without floating point. Null when invalid. */
export function parsePounds(text: string): number | null {
  const cleaned = text.trim().replace(/^£/, '').replace(/,/g, '')
  const match = /^(\d{1,12})(?:\.(\d{1,2}))?$/.exec(cleaned)
  if (!match) return null
  const pence = Number(match[1]) * 100 + Number((match[2] ?? '').padEnd(2, '0'))
  return Number.isSafeInteger(pence) && pence <= MAX_BUDGET_PENCE ? pence : null
}

export const poundsText = (pence: number) => `${Math.floor(pence / 100)}.${String(pence % 100).padStart(2, '0')}`

export function validateRequirements(r: Requirements, knownExclusionIds: readonly string[]): string[] {
  const errors: string[] = []
  if (!Number.isSafeInteger(r.budgetPence) || r.budgetPence < 0 || r.budgetPence > MAX_BUDGET_PENCE) errors.push('Budget must be a whole number of pence between £0 and £100,000,000.')
  if (r.maxTreeCount !== null && (!Number.isSafeInteger(r.maxTreeCount) || r.maxTreeCount < 0 || r.maxTreeCount > 10_000)) errors.push('Maximum tree count must be blank (no limit) or a whole number from 0 to 10,000.')
  const unknown = r.excludedRegionIds.filter(id => !knownExclusionIds.includes(id))
  if (unknown.length) errors.push(`Unknown exclusion region(s): ${unknown.join(', ')}.`)
  return errors
}

export interface FieldChange { readonly path: string; readonly before: unknown; readonly after: unknown }

/** Structural diff of two scenario inputs, as dotted paths. Arrays compare as whole values. */
export function diffInputs(before: unknown, after: unknown, path = ''): FieldChange[] {
  const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)
  if (isObject(before) && isObject(after)) {
    const keys = [...new Set([...Object.keys(before), ...Object.keys(after)])].sort()
    return keys.flatMap(k => diffInputs(before[k], after[k], path ? `${path}.${k}` : k))
  }
  return JSON.stringify(before) === JSON.stringify(after) ? [] : [{ path: path || '(root)', before, after }]
}

export const describeValue = (v: unknown) => (v === undefined ? '—' : v === null ? 'none' : typeof v === 'string' ? v : JSON.stringify(v))

export interface CommitPlan {
  /** Next layout revision, or null when the tree did not move. */
  readonly layout: Layout | null
  readonly input: ScenarioInput_Input
  readonly ifMatch: number
  readonly deadlineRenewedTo: string | null
  readonly changes: readonly FieldChange[]
}

const isoZ = (ms: number) => new Date(ms).toISOString().replace(/\.\d{3}Z$/, 'Z')

/**
 * Build the next accepted scenario input from the user's draft. A moved tree becomes the next
 * immutable layout revision; requirement edits change only the named constraint fields.
 */
export function buildCommit(
  scenario: Scenario, layout: Layout, placementId: string, position: Vec3, nowMs: number, requirements?: Requirements,
  candidate?: { readonly candidate_id: string; readonly location_id: string } | null,
): CommitPlan {
  const ref = scenario.input.proposed_layout_ref
  if (!ref || ref.layout_id !== layout.layout_id || ref.revision !== layout.revision) {
    throw new Error('Scenario does not point at the layout being edited')
  }
  const placement = layout.placements.find(p => p.placement_id === placementId)
  if (!placement) throw new Error(`Unknown placement ${placementId}`)
  const moved = !samePosition(placement.position_enu_m as Vec3, roundPosition(position))
  const ids = candidate ? { candidate_id: candidate.candidate_id, location_id: candidate.location_id } : {}
  const nextLayout: Layout | null = moved
    ? { ...layout, revision: layout.revision + 1, placements: layout.placements.map(p => (p.placement_id === placementId ? { ...p, ...ids, position_enu_m: roundPosition(position) } : p)) }
    : null
  const deadline = Date.parse(scenario.input.search.deadline_utc)
  const deadlineRenewedTo = deadline - nowMs > DEADLINE_MARGIN_MS ? null : isoZ(nowMs + DEADLINE_RENEWAL_MS)
  const constraints = requirements
    ? { ...scenario.input.constraints, budget_pence: requirements.budgetPence, max_tree_count: requirements.maxTreeCount, excluded_region_ids: [...requirements.excludedRegionIds] }
    : scenario.input.constraints
  const input: ScenarioInput_Input = {
    ...(scenario.input as unknown as ScenarioInput_Input),
    constraints,
    proposed_layout_ref: nextLayout ? { layout_id: nextLayout.layout_id, revision: nextLayout.revision } : ref,
    search: deadlineRenewedTo ? { ...scenario.input.search, deadline_utc: deadlineRenewedTo } : scenario.input.search,
  }
  return { layout: nextLayout, input, ifMatch: scenario.revision, deadlineRenewedTo, changes: diffInputs(scenario.input, input) }
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

export interface CatalogueCandidate { readonly candidate_id: string; readonly location_id: string; readonly position_enu_m: readonly number[]; readonly profile_id: string }

/** The catalogue candidate exactly at a position, if any. */
export function candidateAt(catalogue: readonly CatalogueCandidate[], p: readonly number[] | null): CatalogueCandidate | null {
  if (!p) return null
  return catalogue.find(c => samePosition(c.position_enu_m as Vec3, p as Vec3)) ?? null
}

/** Nearest catalogue candidate to a free position (for snapping drags). */
export function nearestCandidate(catalogue: readonly CatalogueCandidate[], p: readonly number[]): CatalogueCandidate | null {
  let best: CatalogueCandidate | null = null
  let bestD = Infinity
  for (const c of catalogue) {
    const d = Math.hypot(c.position_enu_m[0] - p[0], c.position_enu_m[1] - p[1])
    if (d < bestD) { best = c; bestD = d }
  }
  return best
}

/** Nearest candidate strictly in the given ENU direction (within 60 degrees), for keyboard stepping. */
export function stepCandidate(catalogue: readonly CatalogueCandidate[], from: readonly number[], east: number, north: number): CatalogueCandidate | null {
  let best: CatalogueCandidate | null = null
  let bestD = Infinity
  for (const c of catalogue) {
    const dx = c.position_enu_m[0] - from[0]
    const dy = c.position_enu_m[1] - from[1]
    const d = Math.hypot(dx, dy)
    if (d < 1e-9) continue
    if ((dx * east + dy * north) / d < 0.5) continue
    if (d < bestD) { best = c; bestD = d }
  }
  return best
}
