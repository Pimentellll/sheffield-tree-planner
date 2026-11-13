import { describe, expect, it } from 'vitest'
import type { Health, Metric } from '../api/types'
import {
  AGENT_API_UNAVAILABLE_REASON, MODEL_INTERPRETATION_LABEL, agentPanelState, evidenceChain, linkageProblems, metricLabel, metricText, narrativeFigures,
  narrativeView, type ChainJob, type ChainLayout, type ChainResult,
} from './agentEvidence'

// Labelled synthetic test inputs shaped after the backend wire types: 64-hex fingerprints, unique
// metric_instance_ids, metric/unit/weighting pairs from Metric.registry_pair, and non-feasible
// layouts with reasons (contracts/results.py). They are not run through backend validation and are
// not runtime results.
type Delivery = NonNullable<ChainJob['delivery']>
const FP = 'a'.repeat(64)
const FP2 = 'b'.repeat(64)
const ref = { scenario_id: 's1', revision: 3, scope: 'accepted' as const }
let metricSeq = 0
const metric = (over: Partial<Metric> = {}): Metric => ({
  case_id: 'summer', horizon_years: 10, layout_id: 'L1', metric_id: 'additional_shade', metric_instance_id: `m${++metricSeq}`,
  quantity_kind: 'geometric', scenario_ref: ref, target_id: null, unit: 'm2_h', value: 12.34, weighting: 'unweighted', ...over,
})
const energy = (unit: 'kWh' | 'kWh_per_m2', value: number): Metric =>
  metric({ metric_id: 'direct_incident_energy_change', quantity_kind: 'direct_incident_energy', unit, value, weighting: 'unweighted', area_basis: 'surface', aggregation_basis: 'sum' })
const delivery = (over: Partial<Delivery> = {}): Delivery => ({
  delivered_at_utc: '2026-11-13T12:00:00Z', execution_mode: 'live', input_fingerprint: FP, job_id: 'job-1', run_id: 'run-1',
  scenario_id: 's1', scenario_revision: 3, scope: 'accepted', selection_seq: 1, source_job_id: 'job-1', view_slot: 'evaluation', ...over,
})
const job = (over: Partial<ChainJob> = {}): ChainJob => ({
  job_id: 'job-1', status: 'completed', operation: 'evaluate_layout', scenario_id: 's1', scenario_revision: 3, scope: 'accepted', delivery: delivery(), ...over,
})
// evaluate_layout returns comparison_completed with ONE unselected, not-evaluated layout (evaluators/__init__.py ~343-353).
const layout = (over: Partial<ChainLayout> = {}): ChainLayout => ({
  cost_pence: 45000, selected: false, role: 'alternative', feasibility: 'not_evaluated', reasons: ['Constraints not evaluated'],
  scenario_ref: ref, layout: { layout_id: 'L1' }, ...over,
})
const result = (over: Partial<ChainResult> = {}): ChainResult => ({
  run_id: 'run-1', source_job_id: 'job-1', input_fingerprint: FP, input_snapshot_ref: ref, operation: 'evaluate_layout',
  analytical_outcome: 'comparison_completed', metrics: [metric()], missing_metrics: [], layouts: [layout()],
  limitations: ['Synthetic flat site; one-hour sample.'], provenance: { execution_mode: 'live' }, ...over,
})

describe('agentPanelState (no agent API before #73)', () => {
  it('is explicitly unavailable and only promises manual evaluation when the backend offers it', () => {
    const none = agentPanelState(null)
    expect([none.kind, none.manualEvaluateAvailable, none.workerRunning]).toEqual(['unavailable', false, null])
    expect(none.reason.startsWith(AGENT_API_UNAVAILABLE_REASON)).toBe(true)
    expect(none.reason).toContain('not offered by this backend')
    const ok = agentPanelState({ available_operations: ['evaluate_layout', 'search_layouts'], worker_mode: 'background' })
    expect([ok.manualEvaluateAvailable, ok.workerRunning]).toEqual([true, true])
    expect(ok.reason).toContain('Manual evaluation is unaffected')
    expect(ok.reason).not.toContain('manual mode')
    expect(agentPanelState({ available_operations: ['search_layouts'] }).manualEvaluateAvailable).toBe(false)
  })
  it('reports a manual-mode worker and never throws on a malformed health payload', () => {
    const manual = agentPanelState({ available_operations: ['evaluate_layout'], worker_mode: 'manual' })
    expect(manual.workerRunning).toBe(false)
    expect(manual.reason).toContain('manual mode')
    const malformed = { available_operations: null, worker_mode: 42 } as unknown as Health
    expect(() => agentPanelState(malformed)).not.toThrow()
    expect([agentPanelState(malformed).manualEvaluateAvailable, agentPanelState(malformed).workerRunning]).toEqual([false, null])
  })
})

describe('evidenceChain (backend values only)', () => {
  const byKind = (chain: ReturnType<typeof evidenceChain>, kind: string) => (chain.ok ? chain.steps.filter(s => s.kind === kind).map(s => s.value) : null)
  const labels = (chain: ReturnType<typeof evidenceChain>, kind: string) => (chain.ok ? chain.steps.filter(s => s.kind === kind).map(s => s.label) : null)

  it('links job → delivery → result → metric, cost and limitation with the supplied currentness', () => {
    const chain = evidenceChain(job(), result(), 'current')
    expect(chain.ok).toBe(true)
    expect(chain.ok && [chain.outcome, chain.feasible]).toEqual(['comparison_completed', null])
    expect(byKind(chain, 'outcome')).toEqual(['Computed (feasibility shown per layout)'])
    expect(byKind(chain, 'job')).toEqual(['job-1'])
    expect(byKind(chain, 'result')).toEqual(['run-1 · delivered as: Live computation'])
    expect(byKind(chain, 'provenance')).toEqual(['job job-1 · Live computation'])
    expect(byKind(chain, 'currentness')).toEqual(['CURRENT'])
    expect(byKind(chain, 'metric')).toEqual(['12.34 m²·h'])
    // The one evaluated layout's cost, converted from pence once, with the backend's reason.
    expect(byKind(chain, 'cost')).toEqual(['£450.00 · not evaluated · Constraints not evaluated'])
    expect(labels(chain, 'cost')).toEqual(['Cost · alternative layout L1'])
    expect(byKind(chain, 'limitation')).toEqual(['Synthetic flat site; one-hour sample.'])
  })
  it('reports the analytical outcome so an infeasible search is never shown as a success', () => {
    const search = job({ operation: 'search_layouts' })
    const found = evidenceChain(search, result({ operation: 'search_layouts', analytical_outcome: 'feasible_candidate', layouts: [layout({ selected: true, feasibility: 'feasible', reasons: [] })] }), 'current')
    expect(found.ok && [found.feasible, byKind(found, 'outcome'), byKind(found, 'cost')]).toEqual([true, ['Feasible planting layout found'], ['£450.00 · feasible · selected']])
    const infeasible = evidenceChain(search, result({ operation: 'search_layouts', analytical_outcome: 'proven_infeasible_finite_model', layouts: [layout({ feasibility: 'infeasible', reasons: ['budget exceeded'] })] }), 'current')
    expect(infeasible.ok && [infeasible.feasible, byKind(infeasible, 'outcome'), byKind(infeasible, 'cost')])
      .toEqual([false, ['Proven infeasible within the finite model'], ['£450.00 · infeasible · budget exceeded']])
  })
  it('derives feasibility for comparisons from the proposed layouts', () => {
    const compare = job({ operation: 'compare_locations' })
    const baseline = layout({ role: 'baseline', feasibility: 'feasible', reasons: [], layout: { layout_id: 'L0' } })
    const moved = (feasibility: ChainLayout['feasibility']) => layout({ feasibility, reasons: feasibility === 'feasible' ? [] : ['candidate mismatch'] })
    const chain = (alt: ChainLayout) => evidenceChain(compare, result({ operation: 'compare_locations', layouts: [baseline, alt] }), 'current')
    const infeasible = chain(moved('infeasible'))
    expect(infeasible.ok && infeasible.feasible).toBe(false)
    expect(byKind(infeasible, 'cost')).toEqual(['£450.00 · feasible', '£450.00 · infeasible · candidate mismatch'])
    const feasible = chain(moved('feasible'))
    expect(feasible.ok && feasible.feasible).toBe(true)
  })
  it('accepts a cache hit and shows it as cached, keeping the original live computation as provenance', () => {
    const cached = job({ job_id: 'job-2', delivery: delivery({ job_id: 'job-2', execution_mode: 'cached', source_job_id: 'job-1' }) })
    expect(linkageProblems(cached, result())).toEqual([])
    const chain = evidenceChain(cached, result(), 'current')
    expect(byKind(chain, 'result')).toEqual(['run-1 · delivered as: Cached result (exact same inputs)'])
    expect(byKind(chain, 'provenance')).toEqual(['job job-1 · Live computation'])
  })
  it('never upgrades currentness: a superseded result stays SUPERSEDED', () => {
    expect(byKind(evidenceChain(job(), result(), 'superseded'), 'currentness')).toEqual(['SUPERSEDED'])
  })
  it('labels per-target and aggregate rows of the same metric distinctly', () => {
    const r = result({ metrics: [metric(), metric({ target_id: 'bench-1', value: 5 })] })
    expect(labels(evidenceChain(job(), r, 'current'), 'metric')).toEqual([
      'additional_shade · case summer · all targets · layout L1 · geometric',
      'additional_shade · case summer · bench-1 · layout L1 · geometric',
    ])
    expect(metricLabel(metric({ target_id: 'bench-1' }))).toContain('bench-1')
  })
  it('adds the scenario to labels when a result spans several scenarios', () => {
    const alt = { scenario_id: 's2', revision: 1, scope: 'hypothetical' as const }
    const r = result({ operation: 'compare_scenarios', metrics: [metric(), metric({ scenario_ref: alt })], layouts: [layout(), layout({ scenario_ref: alt })] })
    const chain = evidenceChain(job({ operation: 'compare_scenarios' }), r, 'current')
    expect(labels(chain, 'metric')).toEqual([
      'additional_shade · case summer · all targets · layout L1 · geometric · accepted s1 r3',
      'additional_shade · case summer · all targets · layout L1 · geometric · hypothetical s2 r1',
    ])
    expect(labels(chain, 'cost')).toEqual(['Cost · alternative layout L1 · accepted s1 r3', 'Cost · alternative layout L1 · hypothetical s2 r1'])
  })
  it('shows missing metrics as not computed instead of dropping them', () => {
    const r = result({ metrics: [], missing_metrics: [{ metric_id: 'winter_sun_loss', case_id: 'winter', layout_id: 'L1', reason: 'no winter case', scenario_ref: ref }] })
    expect(byKind(evidenceChain(job(), r, 'current'), 'missing-metric')).toEqual(['Not computed: no winter case'])
  })
  it('never renders a malformed cost as a price', () => {
    expect(byKind(evidenceChain(job(), result({ layouts: [layout({ cost_pence: 450.5 })] }), 'current'), 'cost'))
      .toEqual(['450.5 GBP pence (not a valid whole amount) · not evaluated · Constraints not evaluated'])
  })
  it('refuses a result that the job did not deliver, or a live delivery of a non-live result', () => {
    for (const [j, r] of [
      [job({ delivery: null }), result()],
      [job({ status: 'running', delivery: null }), result()],
      [job({ delivery: delivery({ job_id: 'job-9' }) }), result()],
      [job({ delivery: delivery({ run_id: 'run-2' }) }), result()],
      [job(), result({ source_job_id: 'job-2' })],
      [job(), result({ input_fingerprint: FP2 })],
      [job(), result({ input_snapshot_ref: { ...ref, revision: 2 } })],
      [job(), result({ operation: 'search_layouts' })],
      [job(), result({ provenance: { execution_mode: 'recorded' } })],
      [job({ job_id: 'job-2', delivery: delivery({ job_id: 'job-2', execution_mode: 'live', source_job_id: 'job-1' }) }), result()],
    ] as const) {
      const chain = evidenceChain(j, r, 'current')
      expect(chain.ok).toBe(false)
      expect(!chain.ok && chain.problems.length).toBeGreaterThan(0)
    }
  })
})

describe('metricText', () => {
  it('converts integer pence to pounds exactly once and keeps other units', () => {
    expect(metricText({ unit: 'GBP_pence', value: 123456 })).toBe('£1,234.56')
    expect(metricText({ unit: 'GBP_pence', value: 12.5 })).toBe('12.5 GBP pence')
    expect(metricText({ unit: 'm2_h', value: 0 })).toBe('0 m²·h')
  })
})

describe('narrativeFigures (untrusted model text)', () => {
  const statuses = (text: string, r: ChainResult | null = result()) => narrativeFigures(text, r).map(f => [f.text, f.kind, f.status])

  it('flags unsupported and unverified figures, and recognises ones that appear in the result', () => {
    const text = 'Planting here adds 12.3 m²·h of shade for £450.00, cooling the street by 3 °C and saving £1,200 a year (40% more shade).'
    expect(statuses(text)).toEqual([
      ['12.3 m²·h', 'shade_m2_h', 'appears-in-result'],
      ['£450.00', 'money', 'appears-in-result'],
      ['3 °C', 'temperature', 'unsupported'],
      ['£1,200', 'money', 'unverified'],
      ['40%', 'percent', 'unsupported'],
    ])
  })
  it('leaves bare counts, identifiers and clock times alone', () => {
    expect(narrativeFigures('Revision 2 has 3 trees in case C5 at 3 p.m.', result())).toEqual([])
  })
  it('treats every computable figure as unverified when no validated result is attached', () => {
    expect(narrativeFigures('adds 12.3 m²·h, about 3 °C cooler', null).map(f => f.status)).toEqual(['unverified', 'unsupported'])
  })
  it('matches only to the precision the model wrote', () => {
    const only = (text: string) => narrativeFigures(text, result()).map(f => f.status)
    expect(only('12 m²·h')).toEqual(['appears-in-result'])
    expect(only('12.30 m²·h')).toEqual(['unverified'])
    expect(only('£450')).toEqual(['appears-in-result'])
    expect(only('£451')).toEqual(['unverified'])
    expect(only('45000 pence')).toEqual(['appears-in-result'])
    expect(only('45000p')).toEqual(['appears-in-result'])
  })
  it('applies currency scales and signs instead of reading them as £450', () => {
    expect(statuses('£450k')).toEqual([['£450k', 'money', 'unverified']])
    expect(statuses('£1.2m')).toEqual([['£1.2m', 'money', 'unverified']])
    expect(statuses('£450mn')).toEqual([['£450mn', 'money', 'unverified']])
    expect(statuses('£450-million')).toEqual([['£450-million', 'money', 'unverified']])
    expect(statuses('£450 trillion')).toEqual([['£450 trillion', 'money', 'unverified']])
    expect(statuses('−£450')).toEqual([['−£450', 'money', 'unverified']])
  })
  it('caps the rounding of scaled figures at 5% of their value', () => {
    const r = result({ layouts: [layout({ cost_pence: 60_000_000 })] }) // £600,000
    expect(statuses('£1m', r)).toEqual([['£1m', 'money', 'unverified']])
    expect(statuses('£0.6m', r)).toEqual([['£0.6m', 'money', 'appears-in-result']])
  })
  it('flags every common way of writing a temperature', () => {
    for (const text of ['2 deg C', '2℃', '2 ºC', '2 °Celsius', '2 degrees F', '2 kelvin']) {
      expect(narrativeFigures(text, result()).map(f => [f.kind, f.status])).toEqual([['temperature', 'unsupported']])
    }
    expect(statuses('5 percentage points')).toEqual([['5 percentage points', 'percent', 'unsupported']])
  })
  it('never treats foreign currency or unattributable scales as backed by the result', () => {
    expect(statuses('$450')).toEqual([['$450', 'money', 'unverified']])
    expect(statuses('€450')).toEqual([['€450', 'money', 'unverified']])
    expect(statuses('30 degrees')).toEqual([['30 degrees', 'degrees', 'unverified']])
    expect(statuses('2 K')).toEqual([['2 K', 'unknown', 'unverified']])
    expect(statuses('saves 450k a year')).toEqual([['450k', 'unknown', 'unverified']])
    expect(statuses('saves 1.2m a year')).toEqual([['1.2m', 'unknown', 'unverified']])
    expect(statuses('10 thousand trees')).toEqual([['10 thousand', 'count_scale', 'unverified']])
  })
  it('keeps the sign of a currency range to the figure it belongs to', () => {
    expect(statuses('£400-£450')).toEqual([['£400', 'money', 'unverified'], ['£450', 'money', 'appears-in-result']])
  })
  it('reads decimal commas, markdown emphasis, hyphens, m^2 and bare temperature letters', () => {
    expect(statuses('1,5 °C')).toEqual([['1,5 °C', 'temperature', 'unsupported']])
    expect(statuses('2,5 kWh', result({ metrics: [energy('kWh', 2.5)] }))).toEqual([['2,5 kWh', 'energy_kWh', 'appears-in-result']])
    expect(statuses('**2** °C')).toEqual([['2 °C', 'temperature', 'unsupported']])
    expect(statuses('2-degree')).toEqual([['2-degree', 'degrees', 'unverified']])
    expect(statuses('3C')).toEqual([['3C', 'temperature', 'unsupported']])
    expect(statuses('3 Celsius')).toEqual([['3 Celsius', 'temperature', 'unsupported']])
    expect(statuses('2 deg')).toEqual([['2 deg', 'degrees', 'unverified']])
    expect(statuses('–2.5 kWh', result({ metrics: [energy('kWh', -2.5)] }))).toEqual([['–2.5 kWh', 'energy_kWh', 'appears-in-result']])
    expect(statuses('adds 120 m^2 of shade')).toEqual([['120 m^2', 'area_m2', 'unverified']])
    expect(statuses('adds 120 m**2 of shade')).toEqual([['120 m^2', 'area_m2', 'unverified']])
  })
  it('recognises the other units in the wire Metric unit union', () => {
    const r = result({ metrics: [
      metric(),
      metric({ metric_id: 'weighted_shade_utility', quantity_kind: 'weighted_utility', unit: 'weighted_m2_h', value: 12.34, weighting: 'pedestrian_hours_v1' }),
      energy('kWh_per_m2', 0.8),
    ] })
    expect(statuses('12.3 weighted m²·h', r)).toEqual([['12.3 weighted m²·h', 'weighted_shade', 'appears-in-result']])
    expect(statuses('0.8 kWh/m²', r)).toEqual([['0.8 kWh/m²', 'energy_kWh_per_m2', 'appears-in-result']])
    // No registered metric currently emits h or m: Metric.registry_pair in contracts/results.py
    // (~202-224) allows only m2_h, weighted_m2_h, kWh and kWh_per_m2. So these can only be unverified.
    expect(statuses('3.5 h', r)).toEqual([['3.5 h', 'hours', 'unverified']])
    expect(statuses('4.2 m', r)).toEqual([['4.2 m', 'length_m', 'unverified']])
  })
  it('reads ranges and unicode minus signs without inventing negatives', () => {
    expect(statuses('10-12 m²·h')).toEqual([['12 m²·h', 'shade_m2_h', 'appears-in-result']])
    const r = result({ metrics: [energy('kWh', -2.5)] })
    expect(statuses('changes incident energy by −2.5 kWh', r)).toEqual([['−2.5 kWh', 'energy_kWh', 'appears-in-result']])
    // Signs are compared strictly: noisy but safe.
    expect(statuses('reduces energy by 2.5 kWh', r)).toEqual([['2.5 kWh', 'energy_kWh', 'unverified']])
  })
})

describe('narrativeView', () => {
  it('always labels model prose as interpretation and warns on untraceable figures', () => {
    const mixed = narrativeView('adds 12.3 m²·h and cools by 3 °C', result())
    expect(mixed.label).toBe(MODEL_INTERPRETATION_LABEL)
    expect(mixed.needsWarning).toBe(true)
    expect(narrativeView('adds 12.3 m²·h for £450.00', result()).needsWarning).toBe(false)
  })
  it('lets a correct abstention through but catches temperatures the parser cannot read', () => {
    const abstain = narrativeView('I cannot estimate cooling in °C from a shade model.', result())
    expect([abstain.temperatureMentioned, abstain.needsWarning]).toEqual([false, false])
    for (const text of ['cools by .5 °C', 'about 12,3 °C cooler', 'roughly 2°C', 'a **2** °C drop', 'about 3C cooler']) {
      const v = narrativeView(text, result())
      expect([text, v.temperatureMentioned, v.needsWarning]).toEqual([text, true, true])
    }
  })
  it('warns on hours, lengths and degrees; only spelled counts are context', () => {
    const misstated = narrativeView('trees 3 m apart, shading 6 hours of the afternoon', result())
    expect(misstated.figures.map(f => [f.kind, f.contextOnly])).toEqual([['length_m', false], ['hours', false]])
    expect(misstated.needsWarning).toBe(true)
    expect(narrativeView('a 2-degree drop', result()).needsWarning).toBe(true)
    expect(narrativeView('planted about 10 thousand trees', result()).needsWarning).toBe(false)
  })
  it('still warns on kelvin differences, unlabelled money and area claims', () => {
    for (const text of ['cools the street by 2 K', 'saves 450k a year', 'saves 1.2m a year', 'adds 120 m² of shade', 'adds 120 m^2 of shade']) {
      expect([text, narrativeView(text, result()).needsWarning]).toEqual([text, true])
    }
  })
})
