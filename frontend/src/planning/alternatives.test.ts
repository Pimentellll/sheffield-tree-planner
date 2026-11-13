import { describe, expect, it } from 'vitest'
import type { Result, Scenario } from '../api/types'
import { layoutRows, objectiveView, outcomeView, spendText } from './alternatives'
import { formatPence } from './evaluation'

// LABELLED SYNTHETIC TEST INPUT: shaped like the generated Result contract to exercise pure
// view logic. It is not a runtime result and is never rendered by the application.
const ref = { scenario_id: 's', revision: 2, scope: 'accepted' as const }
const placement = (id: string, e: number) => ({ placement_id: id, location_id: id, position_enu_m: [e, 0, 0] as [number, number, number], profile_id: 'p', candidate_id: null, pinned: false })
const evaluated = (id: string, role: 'baseline' | 'reference' | 'alternative', selected: boolean, cost: number, n: number, feasibility: 'feasible' | 'infeasible' | 'not_evaluated') => ({
  role, selected, cost_pence: cost, tree_count: n, feasibility, reasons: feasibility === 'infeasible' ? ['spacing'] : [], scenario_ref: ref,
  layout: { schema_version: '0.1.0', layout_id: id, revision: 1, kind: 'proposed', placements: Array.from({ length: n }, (_, i) => placement(`${id}-${i}`, i)) },
})
const metric = (layout_id: string, case_id: string, value: number) => ({ layout_id, case_id, value, metric_id: 'additional_shade', unit: 'm2_h', quantity_kind: 'geometric' })
const synthetic = {
  analytical_outcome: 'feasible_candidate',
  finite_model_proof: null,
  layouts: [
    evaluated('alt', 'alternative', true, 2400, 2, 'feasible'),
    evaluated('base', 'baseline', false, 0, 0, 'feasible'),
    evaluated('ref', 'reference', false, 3600, 3, 'infeasible'),
  ],
  metrics: [metric('alt', 'c', 4), metric('alt', 'other', 9), metric('ref', 'c', 5)],
  constraints: [
    { layout_id: 'ref', rule: 'spacing', status: 'fail', observed_value: 1, limit: 2, unit: 'm', evidence: [], case_id: null, scenario_ref: ref },
    { layout_id: 'alt', rule: 'budget', status: 'pass', observed_value: 2400, limit: 5000, unit: 'GBP_pence', evidence: [], case_id: null, scenario_ref: ref },
    { layout_id: 'alt', rule: 'winter', status: 'unknown', observed_value: null, limit: null, unit: null, evidence: [], case_id: null, scenario_ref: ref },
  ],
} as unknown as Result
const scenario = { input: { objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'c', quantity_kind: 'geometric' }, constraints: { budget_pence: 5000, max_tree_count: 3 } } } as unknown as Scenario

describe('outcomeView', () => {
  it('never calls a heuristic target miss a proof', () => {
    const v = outcomeView({ analytical_outcome: 'search_exhausted_without_target', finite_model_proof: null })
    expect(v.detail).toMatch(/not a proof/)
    expect(v.proof).toBe('not-claimed')
  })
  it('only says "proven" with a proof record, and flags a bare claim', () => {
    expect(outcomeView({ analytical_outcome: 'proven_infeasible_finite_model', finite_model_proof: { method: 'exhaustive', evidence_ref: 'e1', model_fingerprint: 'f' } }).proof).toBe('proof-record-present')
    const bare = outcomeView({ analytical_outcome: 'proven_infeasible_finite_model', finite_model_proof: null })
    expect(bare.proof).toBe('claimed-without-proof')
    expect(bare.title).toMatch(/without a proof/)
  })
  it('treats zero planting as a valid outcome', () => {
    expect(outcomeView({ analytical_outcome: 'feasible_zero_planting', finite_model_proof: null }).tone).toBe('neutral')
  })
})

describe('layoutRows', () => {
  const rows = layoutRows(synthetic, scenario)
  it('orders baseline, reference, alternative and keeps returned ids', () => {
    expect(rows.map(r => r.layoutId)).toEqual(['base', 'ref', 'alt'])
  })
  it('uses each layout\'s own metric for the primary case', () => {
    expect(rows.find(r => r.layoutId === 'alt')?.metric?.value).toBe(4)
    expect(rows.find(r => r.layoutId === 'base')?.metric).toBeNull()
  })
  it('reports the run snapshot budget, spend, count and constraint status counts', () => {
    const alt = rows.find(r => r.layoutId === 'alt')!
    expect([alt.costPence, alt.budgetPence, alt.treeCount, alt.maxTreeCount]).toEqual([2400, 5000, 2, 3])
    expect(alt.counts).toEqual({ pass: 1, fail: 0, unknown: 1 })
    expect(rows.find(r => r.layoutId === 'ref')?.counts.fail).toBe(1)
    expect(spendText(alt, formatPence)).toBe('£24.00 of £50.00')
    expect(spendText({ costPence: 1, budgetPence: null }, formatPence)).toMatch(/budget unknown/)
  })
})

describe('objectiveView', () => {
  it('describes both objective kinds', () => {
    expect(objectiveView(scenario).text).toMatch(/Most shade within budget/)
    const target = { input: { objective: { kind: 'minimise_cost_for_target', primary_case_id: 'c', quantity_kind: 'geometric', target_gain_m2_h: 3 } } } as unknown as Scenario
    expect(objectiveView(target).target).toBe('3 m²·h')
  })
})
