import { describe, expect, it } from 'vitest'
import type { Result, Scenario } from '../api/types'
import {
  CURRENTNESS_PILL,
  FEASIBILITY_LABEL,
  RANKING_UNAVAILABLE,
  bestCaptionApplies,
  bestLayoutCaption,
  latestSearch,
  layoutCards,
  noFeasibleLayout,
  pendingSearchText,
  scoreNote,
  searchAvailability,
  shadeNote,
} from './alternativesView'
import { formatValue, unitLabel } from './evaluation'
import type { RunRecord } from './useWorkspace'

// LABELLED SYNTHETIC TEST INPUT: shaped like the generated Result contract to exercise pure view
// logic. It is not a runtime result and is never rendered by the application.
const ref = { scenario_id: 's', revision: 2, scope: 'accepted' as const }
const placement = (id: string, e: number) => ({ placement_id: id, location_id: id, position_enu_m: [e, 0, 0] as [number, number, number], profile_id: 'p', candidate_id: null, pinned: false })
const evaluated = (id: string, role: 'reference' | 'alternative', selected: boolean, cost: number, n: number, feasibility: 'feasible' | 'infeasible' | 'not_evaluated') => ({
  role, selected, cost_pence: cost, tree_count: n, feasibility, reasons: [], scenario_ref: ref,
  layout: { schema_version: '0.1.0', layout_id: id, revision: 1, kind: 'proposed', placements: Array.from({ length: n }, (_, i) => placement(`${id}-${i}`, i)) },
})
const metric = (layout_id: string, case_id: string, value: number, metric_id = 'additional_shade', unit = 'm2_h', target_id: string | null = null) => ({ layout_id, case_id, value, metric_id, unit, target_id, quantity_kind: metric_id === 'additional_shade' ? 'geometric' : 'weighted_utility' })
const synthetic = {
  analytical_outcome: 'feasible_candidate',
  finite_model_proof: null,
  layouts: [
    evaluated('alt', 'alternative', true, 2400, 2, 'feasible'),
    evaluated('ref', 'reference', false, 3600, 3, 'feasible'),
  ],
  metrics: [
    // A per-target metric listed before the whole-site one: the card must not depend on order.
    metric('alt', 'c', 99, 'additional_shade', 'm2_h', 'T1'),
    metric('alt', 'c', 4),
    metric('alt', 'c', 7, 'weighted_shade_utility', 'weighted_m2_h'),
    metric('alt', 'other', 9),
    metric('ref', 'other', 5),
  ],
  constraints: [],
} as unknown as Result
const scenario = { input: { objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'c', quantity_kind: 'geometric' }, constraints: { budget_pence: 5000, max_tree_count: 3 } } } as unknown as Scenario

const run = (operation: string, status: string, withResult: boolean) =>
  ({ job: { operation, status }, result: withResult ? { operation } : null, inputScenario: null }) as unknown as RunRecord
const active = (operation: 'search_layouts' | 'evaluate_layout', status: 'queued' | 'running' | 'completed') => ({ operation, status })

describe('searchAvailability', () => {
  it('reports what the backend offers when search is missing', () => {
    expect(searchAvailability(['search_layouts', 'evaluate_layout'])).toEqual({ available: true })
    expect(searchAvailability(['evaluate_layout'])).toEqual({ available: false, offered: 'evaluate_layout' })
    expect(searchAvailability([])).toEqual({ available: false, offered: 'none' })
  })
})

describe('latestSearch', () => {
  const ok = run('search_layouts', 'completed', true)
  const failed = run('search_layouts', 'failed', false)
  it('shows a failure only when it is newer than the stored result', () => {
    expect(latestSearch([failed, ok], null)).toEqual({ record: ok, pending: null, failure: failed })
    expect(latestSearch([ok, failed], null)).toEqual({ record: ok, pending: null, failure: null })
  })
  it('takes a pending search from the active job and hides the older failure while it runs', () => {
    const running = active('search_layouts', 'running')
    expect(latestSearch([failed, ok], running)).toEqual({ record: ok, pending: running, failure: null })
    expect(latestSearch([], active('search_layouts', 'queued')).pending).toEqual({ operation: 'search_layouts', status: 'queued' })
  })
  it('ignores an active job that is another operation or already finished', () => {
    expect(latestSearch([failed], active('evaluate_layout', 'running'))).toEqual({ record: null, pending: null, failure: failed })
    expect(latestSearch([], active('search_layouts', 'completed')).pending).toBeNull()
  })
  it('treats a completed job with no stored result as a failure, and ignores other operations', () => {
    const noResult = run('search_layouts', 'completed', false)
    expect(latestSearch([noResult], null).failure).toBe(noResult)
    expect(latestSearch([run('evaluate_layout', 'failed', false), run('evaluate_layout', 'completed', true)], null)).toEqual({ record: null, pending: null, failure: null })
  })
})

describe('pendingSearchText', () => {
  const job = { status: 'running' as const, cancel_requested: false, scenario_revision: 3 }
  it('describes a followed search by its status', () => {
    expect(pendingSearchText(job, false)).toBe('A search is running on scenario rev 3. Layouts appear here when it completes.')
  })
  it('never calls a search running once its status was lost', () => {
    const lost = pendingSearchText(job, true)
    expect(lost).toMatch(/status is unknown and no result is assumed/)
    expect(lost).not.toMatch(/running/)
  })
  it('says a cancel was requested', () => {
    expect(pendingSearchText({ ...job, cancel_requested: true }, false)).toBe('A search on scenario rev 3 is being cancelled.')
  })
})

describe('CURRENTNESS_PILL', () => {
  it('mirrors the family tones: success, warning, warning, muted', () => {
    expect(CURRENTNESS_PILL).toEqual({ current: 'sp-ok', 'stale-draft': 'sp-warn', 'not-selected': 'sp-warn', superseded: 'sp-muted' })
  })
})

describe('layoutCards', () => {
  const cards = layoutCards(synthetic, scenario)
  it('returns one card per returned layout, reference first, with stored cost and count', () => {
    expect(cards.map(c => [c.layoutId, c.costPence, c.treeCount])).toEqual([['ref', 3600, 3], ['alt', 2400, 2]])
    expect(cards.map(c => c.title)).toEqual(['Reference layout', 'Alternative — selected by search'])
  })
  it('shows only the primary case as shade and labels any other case separately', () => {
    const [reference, alternative] = cards
    expect(alternative.shade?.value).toBe(4)
    expect(alternative.shade?.unit).toBe('m2_h')
    expect(alternative.otherCaseShade).toBeNull()
    expect(shadeNote(alternative)).toBe('case c')
    // layoutRows falls back to another case for `metric`; the card does not present it as primary.
    expect(reference.metric?.case_id).toBe('other')
    expect(reference.shade).toBeNull()
    expect(reference.otherCaseShade?.case_id).toBe('other')
    expect(shadeNote(reference)).toBe('case other, not the primary case (c)')
  })
  it('names the target when only a per-target value exists for the case', () => {
    const perTargetOnly = { ...synthetic, metrics: [metric('alt', 'c', 99, 'additional_shade', 'm2_h', 'T1')] } as unknown as Result
    const alt = layoutCards(perTargetOnly, scenario).find(c => c.layoutId === 'alt')!
    expect(alt.shade?.value).toBe(99)
    expect(shadeNote(alt)).toBe('case c, target T1 only')
  })
  it('keeps the weighted search score apart from physical shade', () => {
    expect(cards[1].score).toMatchObject({ value: 7, unit: 'weighted_m2_h', metric_id: 'weighted_shade_utility' })
    expect(scoreNote(cards[1], formatValue, unitLabel)).toBe('search score 7 weighted m²·h, not physical shade')
    expect(cards[0].score).toBeNull()
    expect(scoreNote(cards[0], formatValue, unitLabel)).toBeNull()
  })
  it('without the run scenario, says the primary case is unknown instead of "not the primary case"', () => {
    const unknown = layoutCards(synthetic, null)
    expect(unknown.every(c => c.primaryCaseId === null && c.shade === null)).toBe(true)
    expect(unknown[1].otherCaseShade?.value).toBe(4)
    expect(shadeNote(unknown[1])).toBe('case c; primary case unknown for this run')
    expect(scoreNote(unknown[1], formatValue, unitLabel)).toBe('search score 7 weighted m²·h (case c), not physical shade')
    expect(unknown[1].budgetPence).toBeNull()
  })
})

describe('noFeasibleLayout', () => {
  it('is true for an empty result or when nothing is feasible', () => {
    expect(noFeasibleLayout([])).toBe(true)
    expect(noFeasibleLayout([{ feasibility: 'infeasible' }, { feasibility: 'not_evaluated' }])).toBe(true)
    expect(noFeasibleLayout([{ feasibility: 'feasible' }, { feasibility: 'infeasible' }])).toBe(false)
  })
})

describe('bestCaptionApplies', () => {
  const feasible = [{ feasibility: 'feasible' as const }]
  it('applies only to a feasible-candidate outcome with a feasible layout', () => {
    expect(bestCaptionApplies('feasible_candidate', feasible)).toBe(true)
    expect(bestCaptionApplies('feasible_candidate', [])).toBe(false)
    expect(bestCaptionApplies('feasible_candidate', [{ feasibility: 'infeasible' }])).toBe(false)
  })
  it('never applies when the target was missed or nothing was eligible, even with feasible layouts', () => {
    expect(bestCaptionApplies('search_exhausted_without_target', feasible)).toBe(false)
    expect(bestCaptionApplies('no_eligible_candidates', feasible)).toBe(false)
  })
})

describe('wording', () => {
  it('names the objective in the caption and never claims an optimum', () => {
    expect(bestLayoutCaption('maximise_shade_under_budget')).toMatch(/^Best evaluated layout under the accepted budget, not a proven optimum\./)
    expect(bestLayoutCaption('minimise_cost_for_target')).toMatch(/^Lowest-cost evaluated layout for the accepted target, not a proven optimum\./)
    expect(bestLayoutCaption(null)).toMatch(/^Best layout this search evaluated, not a proven optimum\./)
  })
  it('uses none of the forbidden words', () => {
    const text = [
      bestLayoutCaption('maximise_shade_under_budget'),
      bestLayoutCaption('minimise_cost_for_target'),
      bestLayoutCaption(null),
      RANKING_UNAVAILABLE,
      ...Object.values(FEASIBILITY_LABEL),
      ...layoutCards(synthetic, scenario).map(c => c.title),
    ].join(' ')
    expect(text).not.toMatch(/optimi[sz]|optimal|even spread/i)
  })
})
