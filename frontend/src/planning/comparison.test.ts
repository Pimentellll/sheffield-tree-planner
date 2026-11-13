import { describe, expect, it } from 'vitest'
import type { Result, Scenario } from '../api/types'
import { compareRuns, deltaRows, pairMetrics, timeBins, winterView } from './comparison'

// LABELLED SYNTHETIC TEST INPUTS shaped like generated contracts, for pure view logic only.
const m = (over: Record<string, unknown>) => ({
  metric_id: 'additional_shade', case_id: 'c', target_id: 't', unit: 'm2_h', quantity_kind: 'geometric', horizon_years: 20,
  area_basis: 'surface', weighting: 'none', value: 0, layout_id: 'L', metric_instance_id: 'mi', scenario_ref: {}, ...over,
})
const layout = (x: number) => ({ layout: { layout_id: 'L', revision: x === 0 ? 1 : 2, placements: [{ placement_id: 'tree-1', position_enu_m: [x, -1, 0] }] } })
const result = (rev: number, metrics: unknown[], x: number) => ({ scenario_id: 's', scenario_revision: rev, metrics, layouts: [layout(x)], constraints: [], missing_metrics: [] }) as unknown as Result
const scenario = (input: Record<string, unknown>) => ({ input: { search: { deadline_utc: 'x' }, ...input } }) as unknown as Scenario

describe('pairMetrics', () => {
  it('pairs only metrics with identical meaning and reports the UI difference', () => {
    const pairs = pairMetrics(result(1, [m({ value: 2 })], 0), result(2, [m({ value: 0 }), m({ horizon_years: 5, value: 1 })], 20))
    const same = pairs.find(p => p.base && p.alternative)!
    expect(same.difference).toBe(-2)
    const only = pairs.find(p => !p.base)!
    expect(only.difference).toBeNull()
    expect(only.note).toMatch(/Only in the alternative/)
  })
  it('never merges different horizons or units', () => {
    const pairs = pairMetrics(result(1, [m({ horizon_years: 5 })], 0), result(2, [m({ horizon_years: 20 })], 0))
    expect(pairs.every(p => p.difference === null)).toBe(true)
  })
})

describe('compareRuns', () => {
  const inputA = { proposed_layout_ref: { layout_id: 'L', revision: 1 }, constraints: { budget_pence: 1 } }
  it('recognises a controlled relocation (one placement moved, nothing else)', () => {
    const c = compareRuns(
      { result: result(1, [], 0), scenario: scenario(inputA) },
      { result: result(2, [], 20), scenario: scenario({ ...inputA, proposed_layout_ref: { layout_id: 'L', revision: 2 } }) },
    )
    expect(c.kind).toBe('controlled-relocation')
    expect(c.movedPlacements).toEqual([{ placementId: 'tree-1', from: [0, -1, 0], to: [20, -1, 0] }])
  })
  it('reports multiple changes when a constraint also changed', () => {
    const c = compareRuns(
      { result: result(1, [], 0), scenario: scenario(inputA) },
      { result: result(2, [], 20), scenario: scenario({ proposed_layout_ref: { layout_id: 'L', revision: 2 }, constraints: { budget_pence: 2 } }) },
    )
    expect(c.kind).toBe('multiple-changes')
    expect(c.changes.map(x => x.path)).toContain('constraints.budget_pence')
  })
})

describe('deltaRows', () => {
  it('resolves backend deltas to their metric instances and flags unresolved ids', () => {
    const r = { metrics: [m({ metric_instance_id: 'a', value: 1 }), m({ metric_instance_id: 'b', value: 3 })], comparison: { mode: 'fixed_layout', changed_inputs: [], deltas: [
      { base_metric_instance_id: 'a', alternative_metric_instance_id: 'b', value: 2, unit: 'm2_h', mode: 'fixed_layout', changed_inputs: ['x'] },
      { base_metric_instance_id: 'a', alternative_metric_instance_id: 'zz', value: 9, unit: 'm2_h', mode: 'fixed_layout', changed_inputs: [] },
    ] } } as unknown as Result
    const rows = deltaRows(r)
    expect(rows[0].resolved && rows[0].base?.value === 1 && rows[0].alternative?.value === 3).toBe(true)
    expect(rows[1].resolved).toBe(false)
  })
})

describe('timeBins and winterView', () => {
  it('labels analysis bins in UTC and the display zone', () => {
    const bins = timeBins({ time_bins: [{ midpoint_utc: '2026-07-01T12:00:00Z', duration_h: 1 }] } as never, 'Europe/London')
    expect(bins[0].local).toMatch(/13:00/)
    expect(bins[0].zone).toBe('Europe/London')
    expect(timeBins({ time_bins: [{ midpoint_utc: '2026-07-01T12:00:00Z', duration_h: 1 }] } as never, 'Not/AZone')[0].zone).toBe('UTC')
  })
  it('says a winter trade-off is not in the scenario rather than implying zero loss', () => {
    const s = { input: { evaluation_cases: [{ role: 'benefit', case_id: 'c' }], constraints: { winter_limits: [] } } } as unknown as Scenario
    expect(winterView(s, null).status).toBe('not-in-scenario')
    const w = { input: { evaluation_cases: [{ role: 'winter_check', case_id: 'w' }], constraints: { winter_limits: [] } } } as unknown as Scenario
    expect(winterView(w, null).status).toBe('no-result')
    const reported = winterView(w, { metrics: [m({ metric_id: 'winter_sun_loss', case_id: 'w', value: 1 })], constraints: [], missing_metrics: [] } as unknown as Result)
    expect(reported.metrics).toHaveLength(1)
  })
})
