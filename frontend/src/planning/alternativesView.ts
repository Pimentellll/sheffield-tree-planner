import type { Job, Metric, Result, Scenario } from '../api/types'
import { ROLE_LABEL, layoutRows } from './alternatives'
import type { LayoutRow } from './alternatives'
import type { Currentness } from './evaluation'
import type { RunRecord } from './useWorkspace'

/**
 * View logic for the Product Vision v2 alternatives panel (C05). It builds on layoutRows and adds
 * only what the panel must say more strictly: which case a shade number belongs to, and that the
 * weighted search score is not physical shade. The search returns whole evaluated layouts (today a
 * reference and a selected alternative); it never ranks individual candidates.
 */

export type SearchAvailability =
  | { readonly available: true }
  | { readonly available: false; readonly offered: string }

export function searchAvailability(availableOperations: readonly string[]): SearchAvailability {
  return availableOperations.includes('search_layouts')
    ? { available: true }
    : { available: false, offered: availableOperations.join(', ') || 'none' }
}

export interface LatestSearch<J> {
  /** Newest search run with a stored result. */
  readonly record: RunRecord | null
  /** The workspace's active job, when it is a queued or running search (or one whose status was lost). */
  readonly pending: J | null
  /**
   * A search newer than that result that ended without one (failed, cancelled, or no result
   * stored). Hidden while a newer search is pending, since that search supersedes it.
   */
  readonly failure: RunRecord | null
}

/**
 * `runs` is newest first and holds only finished jobs, as the workspace keeps it; an in-flight
 * job is only ever the workspace's `activeJob`. Between a job finishing and its record landing in
 * `runs` there is a brief moment with neither; the older state stays visible until it lands.
 */
export function latestSearch<J extends Pick<Job, 'operation' | 'status'>>(runs: readonly RunRecord[], activeJob: J | null): LatestSearch<J> {
  const pending = activeJob && activeJob.operation === 'search_layouts' && (activeJob.status === 'queued' || activeJob.status === 'running')
    ? activeJob
    : null
  const recordIndex = runs.findIndex(r => r.result?.operation === 'search_layouts')
  const failureIndex = runs.findIndex((r, i) => r.job.operation === 'search_layouts' && !r.result && (recordIndex < 0 || i < recordIndex))
  return {
    record: recordIndex >= 0 ? runs[recordIndex] : null,
    pending,
    failure: !pending && failureIndex >= 0 ? runs[failureIndex] : null,
  }
}

/**
 * What to say about an in-flight search. A job whose status could not be followed is never
 * described as running (the workspace's rule for jobStatusLost); a cancel request says so.
 */
export function pendingSearchText(job: Pick<Job, 'status' | 'cancel_requested' | 'scenario_revision'>, statusLost: boolean): string {
  if (statusLost) return `Contact was lost while following a search on scenario rev ${job.scenario_revision}. Its status is unknown and no result is assumed.`
  if (job.cancel_requested) return `A search on scenario rev ${job.scenario_revision} is being cancelled.`
  return `A search is ${job.status} on scenario rev ${job.scenario_revision}. Layouts appear here when it completes.`
}

/** Status-pill tone per currentness, mirroring the family's CURRENTNESS_TONE in Panels.tsx. */
export const CURRENTNESS_PILL: Record<Currentness, string> = {
  current: 'sp-ok',
  'stale-draft': 'sp-warn',
  'not-selected': 'sp-warn',
  superseded: 'sp-muted',
}

export interface LayoutCard extends LayoutRow {
  /** Role label; the layout the search selected says so. */
  readonly title: string
  readonly primaryCaseId: string | null
  /** Unweighted additional shade for the primary case only. Never another case's value. */
  readonly shade: Metric | null
  /** Set only when no primary-case shade is shown: another case's value, shown with `shadeNote`. */
  readonly otherCaseShade: Metric | null
  /** Weighted search score for the primary case. It is a score, not physical shade. */
  readonly score: Metric | null
}

/**
 * Prefer the whole-site metric (target_id null), as the backend's own target check does, over the
 * per-target ones that share its case and metric id. Falls back to the first only if no whole-site
 * metric exists, so the choice never depends on the order the metrics arrive in.
 */
function wholeSiteFirst(metrics: readonly Metric[]): Metric | null {
  return metrics.find(m => m.target_id === null) ?? metrics[0] ?? null
}

/** One card per layout the result returned, in layoutRows order. Costs are the stored cost_pence. */
export function layoutCards(result: Result, inputScenario: Pick<Scenario, 'input'> | null): LayoutCard[] {
  const primaryCaseId = inputScenario?.input.objective.primary_case_id ?? null
  return layoutRows(result, inputScenario).map(row => {
    const own = result.metrics.filter(m => m.layout_id === row.layoutId)
    const shades = own.filter(m => m.metric_id === 'additional_shade')
    const scores = own.filter(m => m.metric_id === 'weighted_shade_utility')
    const shade = primaryCaseId === null ? null : wholeSiteFirst(shades.filter(m => m.case_id === primaryCaseId))
    return {
      ...row,
      title: `${ROLE_LABEL[row.role]}${row.selected ? ' — selected by search' : ''}`,
      primaryCaseId,
      shade,
      otherCaseShade: shade ? null : wholeSiteFirst(shades),
      score: wholeSiteFirst(primaryCaseId === null ? scores : scores.filter(m => m.case_id === primaryCaseId)),
    }
  })
}

/**
 * The "best evaluated layout" caption applies only when the search reports a feasible candidate
 * and returned at least one feasible layout; a missed target or no eligible candidates never gets it.
 */
export function bestCaptionApplies(outcome: Result['analytical_outcome'], cards: readonly Pick<LayoutCard, 'feasibility'>[]): boolean {
  return outcome === 'feasible_candidate' && cards.length > 0 && !noFeasibleLayout(cards)
}

/** The case line under a shade value: says plainly when it is not, or may not be, the primary case. */
export function shadeNote(card: Pick<LayoutCard, 'shade' | 'otherCaseShade' | 'primaryCaseId'>): string | null {
  if (card.shade) return caseLabel(card.shade)
  if (!card.otherCaseShade) return null
  return card.primaryCaseId === null
    ? `${caseLabel(card.otherCaseShade)}; primary case unknown for this run`
    : `${caseLabel(card.otherCaseShade)}, not the primary case (${card.primaryCaseId})`
}

/** A per-target value (only shown when no whole-site metric exists) names its target. */
const caseLabel = (m: Pick<Metric, 'case_id' | 'target_id'>) => (m.target_id === null ? `case ${m.case_id}` : `case ${m.case_id}, target ${m.target_id} only`)

/** The weighted score line, labelled as a score; names its case when the primary case is unknown. */
export function scoreNote(card: Pick<LayoutCard, 'score' | 'primaryCaseId'>, format: (v: number) => string, unit: (u: Metric['unit']) => string): string | null {
  if (!card.score) return null
  const which = card.primaryCaseId === null ? ` (case ${card.score.case_id})` : ''
  return `search score ${format(card.score.value)} ${unit(card.score.unit)}${which}, not physical shade`
}

/** True when the search returned no layout the model marked feasible. */
export function noFeasibleLayout(cards: readonly Pick<LayoutCard, 'feasibility'>[]): boolean {
  return cards.every(c => c.feasibility !== 'feasible')
}

/**
 * The caption under the layouts, shown only where bestCaptionApplies (a feasible-candidate outcome
 * with at least one feasible layout). The search compares whole layouts and proves no optimum.
 */
export function bestLayoutCaption(objective: Scenario['input']['objective']['kind'] | null): string {
  const lead = objective === 'minimise_cost_for_target'
    ? 'Lowest-cost evaluated layout for the accepted target, not a proven optimum.'
    : objective === 'maximise_shade_under_budget'
      ? 'Best evaluated layout under the accepted budget, not a proven optimum.'
      : 'Best layout this search evaluated, not a proven optimum.'
  return `${lead} Only the layouts this search returned are shown.`
}

export const RANKING_UNAVAILABLE =
  'Candidate ranking is not available: this search reports whole layouts, not shade per candidate position.'

export const FEASIBILITY_LABEL: Record<LayoutCard['feasibility'], string> = {
  feasible: 'FEASIBLE',
  infeasible: 'INFEASIBLE',
  not_evaluated: 'NOT EVALUATED',
}

export const FEASIBILITY_PILL: Record<LayoutCard['feasibility'], string> = {
  feasible: 'sp-ok',
  infeasible: 'sp-warn',
  not_evaluated: 'sp-muted',
}
