import { describe, expect, it } from 'vitest'
import type { Layout, Result, Scenario, SiteBundle, TreeProfile, Vec3 } from '../api/types'
import type { Currentness } from './evaluation'
import {
  CONSTRAINTS_LAYOUT_LEVEL, MARGINAL_NOT_CALCULATED, NOT_LOADED, NOT_RECORDED, describeAttenuation, describeConstraint, formatEnu, inspectTree,
  layoutEvidence, metres, type TreeEvidence, type TreeInspectorInput,
} from './treeInspector'

// LABELLED SYNTHETIC TEST INPUT: shaped like the generated contracts to exercise pure view logic.
// None of it is a runtime result, Sheffield data or a computed metric, and the app never renders it.

const layout = {
  schema_version: '0.1.0',
  layout_id: 'layout-a',
  revision: 2,
  kind: 'proposed',
  placements: [
    { placement_id: 'p-1', location_id: 'loc-1', candidate_id: 'cand-1', profile_id: 'prof-m', pinned: false, position_enu_m: [4, -2.5, 0] },
    { placement_id: 'p-free', location_id: 'loc-9', candidate_id: null, profile_id: 'prof-x', pinned: true, position_enu_m: [0, 0, 0] },
  ],
} as unknown as Layout

const catalogue = [
  { candidate_id: 'cand-1', location_id: 'loc-1', profile_id: 'prof-m', plantability_status: 'provisional', position_enu_m: [4, -2.5, 0], source_ids: ['s1', 's2'], assumption_ids: [] },
  { candidate_id: 'cand-2', location_id: 'loc-2', profile_id: 'prof-m', plantability_status: 'excluded', position_enu_m: [9, 9, 0], source_ids: [], assumption_ids: [] },
] as unknown as SiteBundle['candidate_catalogue']

const profile = {
  profile_id: 'prof-m',
  species_size_label: 'generic medium broadleaf',
  cost_pence: 145_000,
  cost_scope: 'scenario unit rate',
  price_date: '2026-01-01',
  library_revision: 3,
  source_ids: ['src'],
  assumption_ids: [],
  states: {
    mature: { horizon_years: 10, crown_radii_m: [3, 3, 2.5], crown_center_height_m: 5.6, trunk_height_m: 3.1, trunk_radius_m: 0.15, leaf_state: 'leaf-on', attenuation: { mode: 'opaque' } },
    planted: { horizon_years: 0, crown_radii_m: [0.9, 0.9, 0.8], crown_center_height_m: 2.4, trunk_height_m: 1.5, trunk_radius_m: 0.04, leaf_state: '', attenuation: { mode: 'fixed_crossing', transmission: null } },
  },
} as unknown as TreeProfile

const scenario = {
  scenario_id: 'scn-1',
  revision: 5,
  scope: 'accepted',
  input: {
    proposed_layout_ref: { layout_id: 'layout-a', revision: 2 },
    objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'summer', quantity_kind: 'geometric' },
    evaluation_cases: [
      { case_id: 'summer', role: 'benefit', profile_state: 'mature' },
      { case_id: 'winter', role: 'winter_check', profile_state: 'mature' },
    ],
  },
} as unknown as Scenario

const ref5 = { scenario_id: 'scn-1', revision: 5, scope: 'accepted' }
const refAlt = { scenario_id: 'scn-alt', revision: 1, scope: 'hypothetical' }
const evaluatedA = { layout, scenario_ref: ref5, feasibility: 'infeasible', reasons: ['winter loss:T1 exceeds limit'], cost_pence: 145_000, tree_count: 2, role: 'alternative', selected: true }
const result = (runId: string, layouts: unknown[], constraints: unknown[] = [], operation = 'evaluate_layout') =>
  ({ run_id: runId, operation, layouts, constraints, metrics: [{ metric_id: 'additional_shade', value: 812, unit: 'm2_h' }] }) as unknown as Result
const run = (r: Result | null, mode: string | null = 'live') =>
  ({ job: { delivery: mode ? { execution_mode: mode } : null }, result: r }) as unknown as { job: { delivery: null }; result: Result | null }
const asEvidence = (e: object) => e as unknown as TreeEvidence

const base: TreeInspectorInput = { placementId: 'p-1', layout, catalogue, profiles: [profile], scenario, evidence: null, draft: null }
const view = (over: Partial<TreeInspectorInput> = {}) => {
  const v = inspectTree({ ...base, ...over })
  if (v.kind !== 'tree') throw new Error(`expected a tree view, got ${v.kind}`)
  return v
}
const value = (rows: readonly { label: string; value: string }[], label: string) => rows.find(r => r.label === label)?.value

describe('inspectTree: selection states', () => {
  it('shows an empty state when nothing is selected or no layout is loaded', () => {
    expect(inspectTree({ ...base, placementId: null }).kind).toBe('empty')
    expect(inspectTree({ ...base, layout: null }).kind).toBe('empty')
  })
  it('refuses a placement id that is not in this layout revision', () => {
    const v = inspectTree({ ...base, placementId: 'p-gone' })
    expect(v.kind).toBe('missing')
    expect(v.kind === 'missing' && v.detail).toContain('layout-a revision 2')
  })
})

describe('inspectTree: identity and position come from the placement and catalogue', () => {
  it('reads ids, plantability and the scenario revision the layout belongs to', () => {
    const v = view()
    expect(v.title).toBe('p-1')
    expect(v.subtitle).toBe('candidate cand-1 · not pinned')
    expect(v.badge).toEqual({ label: 'REV 5', tone: 'ok' })
    expect(value(v.identity, 'Location')).toBe('loc-1')
    expect(v.identity.find(r => r.label === 'Plantability')).toMatchObject({ value: 'Provisional position', tone: 'warn' })
    expect(value(v.identity, 'Position sources')).toBe('2 sources')
    expect(value(v.identity, 'Scenario')).toBe('scn-1 · rev 5 (accepted)')
    expect(value(v.position, 'Position (ENU)')).toBe('E 4 m · N -2.5 m · U 0 m')
  })
  it('says Not recorded for a free placement with no catalogue entry, and Not loaded for its profile', () => {
    const v = view({ placementId: 'p-free' })
    expect(v.subtitle).toBe('no catalogue candidate · pinned')
    expect(value(v.identity, 'Catalogue candidate')).toBe(NOT_RECORDED)
    expect(value(v.identity, 'Plantability')).toBe(NOT_RECORDED)
    expect(value(v.profile, 'Profile')).toBe('prof-x · details not loaded')
    expect(v.states).toEqual([])
  })
  it('flags a layout that is not the scenario\'s proposed layout and drops the revision badge', () => {
    const v = view({ layout: { ...layout, revision: 1 } as Layout })
    expect(v.badge).toEqual({ label: 'LAYOUT REV 1', tone: 'muted' })
    expect(v.identity.find(r => r.label === 'Scenario')).toMatchObject({ value: 'scn-1 · rev 5 (accepted) · not its proposed layout', tone: 'warn' })
    expect(value(view({ scenario: null }).identity, 'Scenario')).toBe(NOT_LOADED)
  })
  it('shows an unaccepted draft position only for its own placement and only when it differs', () => {
    expect(view({ draft: { placementId: 'p-1', position: [4, -2.5, 0] as Vec3 } }).position).toHaveLength(1)
    expect(view({ placementId: 'p-free', draft: { placementId: 'p-1', position: [5, -2.5, 0] as Vec3 } }).position).toHaveLength(1)
    const moved = view({ draft: { placementId: 'p-1', position: [5, -2.5, 0] as Vec3 } }).position[1]
    expect(moved).toMatchObject({ label: 'Draft position', tone: 'warn', tag: 'DRAFT', value: 'E 5 m · N -2.5 m · U 0 m · not accepted' })
  })
})

describe('inspectTree: no per-tree shade figure (register item D)', () => {
  it('always reports marginal shade as not calculated, even when a result with metrics exists', () => {
    const evidence = asEvidence({ result: result('run-1', [evaluatedA]), evaluated: evaluatedA, currentness: 'current', deliveryMode: 'live' })
    for (const v of [view(), view({ evidence })]) {
      expect(v.marginal.value).toBe(MARGINAL_NOT_CALCULATED)
      expect(v.marginal.value).toContain('no remove-one operation exists')
      expect(v.marginal.tag).toBe('NOT COMPUTED')
      expect(v.marginal.value).not.toMatch(/\d/)
    }
  })
})

describe('inspectTree: profile and crown states', () => {
  it('tags cost as an assumption and lists states by horizon, marking the primary case', () => {
    const v = view()
    expect(v.profile.find(r => r.label === 'Upfront cost')).toMatchObject({ value: '£1,450.00 · scenario unit rate', tag: 'ASSUMPTION' })
    expect(value(v.profile, 'Profile assumptions')).toBe(NOT_RECORDED)
    expect(v.states.map(s => s.key)).toEqual(['planted', 'mature'])
    const [planted, mature] = v.states
    expect(mature).toMatchObject({ primary: true, usedBy: 'summer (benefit), winter (winter_check)', crown: 'Crown radii 3 / 3 / 2.5 m · centre 5.6 m', light: 'opaque crown (assumed)' })
    expect(planted).toMatchObject({ primary: false, usedBy: 'No evaluation case uses this state', light: 'fixed transmission, value not recorded' })
    expect(planted.trunk).toContain(`leaves ${NOT_RECORDED}`)
  })
})

describe('inspectTree: stored evaluation of this exact layout and scenario', () => {
  it('says there is none for this layout and scenario revision', () => {
    const v = view()
    expect(v.evaluation).toEqual([])
    expect(v.evaluationNote).toBe('No stored evaluation of this layout revision under scenario revision 5 yet. Feasibility and constraints appear after one.')
    expect(v.constraints).toEqual([])
  })
  it('shows whole-layout feasibility and only this layout and scenario\'s constraints, labelled layout-level', () => {
    const constraints = [
      { layout_id: 'layout-a', scenario_ref: ref5, rule: 'budget', status: 'pass', observed_value: 145_000, limit: 7_500_000, unit: 'GBP_pence', case_id: null },
      { layout_id: 'layout-a', scenario_ref: ref5, rule: 'winter loss:T1', status: 'fail', observed_value: 74, limit: 60, unit: 'm2_h', case_id: 'winter' },
      { layout_id: 'layout-a', scenario_ref: ref5, rule: 'spacing and conflicts', status: 'unknown', observed_value: null, limit: null, unit: null, case_id: null },
      { layout_id: 'layout-a', scenario_ref: refAlt, rule: 'budget', status: 'fail', observed_value: 1, limit: 0, unit: 'GBP_pence', case_id: null },
      { layout_id: 'other', scenario_ref: ref5, rule: 'budget', status: 'pass', observed_value: 1, limit: 2, unit: 'GBP_pence', case_id: null },
    ]
    const evidence = asEvidence({ result: result('run-0123456789abcdef', [evaluatedA], constraints), evaluated: evaluatedA, currentness: 'superseded', deliveryMode: 'live' })
    const v = view({ evidence })
    expect(v.evaluation.find(r => r.label === 'Result')).toMatchObject({ value: 'SUPERSEDED · run run-012345…', tone: 'warn' })
    expect(v.evaluation.find(r => r.label === 'Delivered as')).toMatchObject({ value: 'Live computation', tone: 'plain' })
    expect(v.evaluation.find(r => r.label === 'Layout feasibility')).toMatchObject({ value: 'Infeasible (whole layout)', tone: 'bad' })
    expect(v.evaluation.find(r => r.label === 'Layout cost')).toMatchObject({ value: '£1,450.00 · whole layout', tag: 'ASSUMPTION' })
    expect(value(v.evaluation, 'Reasons')).toBe('winter loss:T1 exceeds limit')
    expect(v.constraintNote).toBe(CONSTRAINTS_LAYOUT_LEVEL)
    expect(v.constraints.map(c => [c.rule, c.statusLabel, c.detail])).toEqual([
      ['budget', 'Pass', 'observed £1,450.00 · limit £75,000.00'],
      ['winter loss:T1', 'Fail', 'observed 74 m²·h · limit 60 m²·h · case winter'],
      ['spacing and conflicts', 'Unknown', null],
    ])
  })
  it('labels a non-live delivery with a warning, and an unknown one as Not recorded (CONTRACTS: delivery mode)', () => {
    const at = (deliveryMode: string | null) => view({ evidence: asEvidence({ result: result('r', [evaluatedA]), evaluated: evaluatedA, currentness: 'current', deliveryMode }) })
    expect(at('cached').evaluation.find(r => r.label === 'Delivered as')).toMatchObject({ value: 'Cached result (exact same inputs)', tone: 'warn' })
    expect(at(null).evaluation.find(r => r.label === 'Delivered as')).toMatchObject({ value: NOT_RECORDED, tone: 'muted' })
  })
})

describe('layoutEvidence', () => {
  const current = (r: Result): Currentness => (r.run_id === 'selected' ? 'current' : 'not-selected')
  const other = { ...evaluatedA, layout: { ...layout, revision: 1 } }
  it('prefers the backend-selected run over a newer late arrival when both evaluated the layout', () => {
    const runs = [run(result('late-old', [evaluatedA])), run(result('selected', [evaluatedA]), 'cached')]
    expect(layoutEvidence(runs, layout, scenario, current, 'selected')).toMatchObject({ result: { run_id: 'selected' }, currentness: 'current', deliveryMode: 'cached' })
    expect(layoutEvidence(runs, layout, scenario, current)).toMatchObject({ result: { run_id: 'late-old' }, currentness: 'not-selected', deliveryMode: 'live' })
  })
  it('falls back to the newest matching run when the selected one evaluated another revision', () => {
    const runs = [run(null, null), run(result('selected', [other])), run(result('match', [evaluatedA]))]
    expect(layoutEvidence(runs, layout, scenario, current, 'selected')?.result.run_id).toBe('match')
  })
  it('never takes a fixed-layout compare_scenarios run, even when it is selected and newest (-bc review)', () => {
    const baseEntry = { ...evaluatedA, feasibility: 'feasible', reasons: [] }
    const alternativeEntry = { ...evaluatedA, scenario_ref: refAlt, feasibility: 'feasible', reasons: [], cost_pence: 1 }
    const comparison = result('selected', [baseEntry, alternativeEntry], [], 'compare_scenarios')
    expect(layoutEvidence([run(comparison)], layout, scenario, current, 'selected')).toBeNull()
    const evaluation = result('eval', [evaluatedA])
    expect(layoutEvidence([run(comparison), run(evaluation)], layout, scenario, current, 'selected')?.result.run_id).toBe('eval')
  })
  it('ignores an evaluation of the same layout under another scenario revision', () => {
    const olderScenario = { ...evaluatedA, scenario_ref: { ...ref5, revision: 4 } }
    expect(layoutEvidence([run(result('r', [olderScenario]))], layout, scenario, current)).toBeNull()
    expect(layoutEvidence([run(result('r', [evaluatedA]))], layout, null, current)).toBeNull()
  })
  it('returns null for no layout or no run of this exact layout revision', () => {
    expect(layoutEvidence([run(result('r', [evaluatedA]))], null, scenario, current)).toBeNull()
    expect(layoutEvidence([run(result('r', [other]))], layout, scenario, current)).toBeNull()
  })
})

describe('formatting helpers', () => {
  it('rounds positions to millimetres without negative zero', () => {
    expect(metres(-0)).toBe('0')
    expect(metres(1.23456)).toBe('1.235')
    expect(formatEnu([0.1 + 0.2, -0.0004, 12])).toBe('E 0.3 m · N 0 m · U 12 m')
  })
  it('describes attenuation and keeps small constraint values instead of rounding them to 0', () => {
    expect(describeAttenuation({ mode: 'fixed_crossing', transmission: 0.3 })).toBe('fixed transmission 0.3 (assumed)')
    expect(describeConstraint({ rule: 'r', status: 'unknown', observed_value: 2, limit: null, unit: 'm', case_id: null } as never).detail).toBe('observed 2 m')
    expect(describeConstraint({ rule: 'r', status: 'pass', observed_value: 0.0004, limit: 0.002, unit: 'kWh_per_m2', case_id: null } as never).detail)
      .toBe('observed 0.0004 kWh/m² · limit 0.002 kWh/m²')
  })
})
