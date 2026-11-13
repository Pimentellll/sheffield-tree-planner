import { describe, expect, it } from 'vitest'
import type { Metric } from '../api/types'
import {
  AGENT_API_UNAVAILABLE_REASON, MODEL_INTERPRETATION_LABEL, agentPanelState, evidenceChain, linkageProblems, metricText, narrativeFigures, narrativeView,
  type ChainJob, type ChainResult,
} from './agentEvidence'

// Labelled synthetic test inputs shaped like the backend wire types. Not runtime results.
const ref = { scenario_id: 's1', revision: 3, scope: 'accepted' as const }
const metric = (over: Partial<Metric> = {}): Metric => ({
  case_id: 'summer', horizon_years: 10, layout_id: 'L1', metric_id: 'additional_shade', metric_instance_id: 'm1',
  quantity_kind: 'geometric', scenario_ref: ref, target_id: null, unit: 'm2_h', value: 12.34, weighting: 'none', ...over,
})
const job = (over: Partial<ChainJob> = {}): ChainJob => ({
  job_id: 'job-1', status: 'completed', run_id: 'run-1', input_fingerprint: 'fp-1', scenario_id: 's1', scenario_revision: 3, scope: 'accepted',
  operation: 'evaluate_layout', ...over,
})
const result = (over: Partial<ChainResult> = {}): ChainResult => ({
  run_id: 'run-1', source_job_id: 'job-1', input_fingerprint: 'fp-1', scenario_id: 's1', scenario_revision: 3, scope: 'accepted', operation: 'evaluate_layout',
  metrics: [metric()], missing_metrics: [], layouts: [{ cost_pence: 45000, selected: true }, { cost_pence: 99900, selected: false }],
  limitations: ['Synthetic flat site; one-hour sample.'], provenance: { execution_mode: 'live' }, ...over,
})

describe('agentPanelState (no agent API before #73)', () => {
  it('is explicitly unavailable and never offers a transcript', () => {
    const state = agentPanelState(null)
    expect(state).toEqual({ kind: 'unavailable', reason: AGENT_API_UNAVAILABLE_REASON, manualEvaluateAvailable: false })
  })
  it('reports the manual fallback only when the backend offers evaluate_layout', () => {
    expect(agentPanelState({ available_operations: ['evaluate_layout', 'search_layouts'] }).manualEvaluateAvailable).toBe(true)
    expect(agentPanelState({ available_operations: ['search_layouts'] }).manualEvaluateAvailable).toBe(false)
  })
})

describe('evidenceChain (backend values only)', () => {
  it('links job → result → metric, cost and limitation with the supplied currentness', () => {
    const chain = evidenceChain(job(), result(), 'current')
    expect(chain.ok).toBe(true)
    if (!chain.ok) return
    const byKind = (kind: string) => chain.steps.filter(s => s.kind === kind).map(s => s.value)
    expect(byKind('job')).toEqual(['job-1'])
    expect(byKind('result')).toEqual(['run-1 · Live computation'])
    expect(byKind('currentness')).toEqual(['CURRENT'])
    expect(byKind('metric')).toEqual(['12.34 m²·h'])
    expect(byKind('cost')).toEqual(['£450.00']) // selected layout only, converted from pence once
    expect(byKind('limitation')).toEqual(['Synthetic flat site; one-hour sample.'])
  })
  it('never upgrades currentness: a superseded result stays SUPERSEDED', () => {
    const chain = evidenceChain(job(), result(), 'superseded')
    expect(chain.ok && chain.steps.find(s => s.kind === 'currentness')?.value).toBe('SUPERSEDED')
  })
  it('shows missing metrics as not computed instead of dropping them', () => {
    const chain = evidenceChain(job(), result({ metrics: [], missing_metrics: [{ metric_id: 'winter_sun_loss', case_id: 'winter', reason: 'no winter case' }] }), 'current')
    expect(chain.ok && chain.steps.filter(s => s.kind === 'missing-metric').map(s => s.value)).toEqual(['Not computed: no winter case'])
  })
  it('refuses a result that does not belong to the job', () => {
    expect(linkageProblems(job(), result())).toEqual([])
    for (const [j, r] of [
      [job(), result({ source_job_id: 'job-2' })],
      [job(), result({ input_fingerprint: 'fp-2' })],
      [job({ run_id: 'run-2' }), result()],
      [job({ status: 'running', run_id: null }), result()],
      [job(), result({ scenario_revision: 2 })],
      [job(), result({ operation: 'search_layouts' })],
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
  it('applies currency scale words instead of reading £450k as £450', () => {
    expect(statuses('£450k')).toEqual([['£450k', 'money', 'unverified']])
    expect(statuses('£1.2m')).toEqual([['£1.2m', 'money', 'unverified']])
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
    expect(statuses('30 degrees')).toEqual([['30 degrees', 'unknown', 'unverified']])
    expect(statuses('2 K')).toEqual([['2 K', 'unknown', 'unverified']])
  })
  it('recognises the other units the backend computes', () => {
    const r = result({ metrics: [
      metric({ unit: 'h', value: 3.5 }), metric({ unit: 'm', value: 4.2 }),
      metric({ metric_id: 'weighted_shade_utility', quantity_kind: 'weighted_utility', unit: 'weighted_m2_h', value: 12.34 }),
      metric({ metric_id: 'direct_incident_energy_change', quantity_kind: 'direct_incident_energy', unit: 'kWh_per_m2', value: 0.8 }),
    ] })
    expect(statuses('3.5 h', r)).toEqual([['3.5 h', 'hours', 'appears-in-result']])
    expect(statuses('4.2 m', r)).toEqual([['4.2 m', 'length_m', 'appears-in-result']])
    expect(statuses('12.3 weighted m²·h', r)).toEqual([['12.3 weighted m²·h', 'weighted_shade', 'appears-in-result']])
    expect(statuses('0.8 kWh/m²', r)).toEqual([['0.8 kWh/m²', 'energy_kWh_per_m2', 'appears-in-result']])
  })
  it('reads ranges and unicode minus signs without inventing negatives', () => {
    expect(statuses('10-12 m²·h')).toEqual([['12 m²·h', 'shade_m2_h', 'appears-in-result']])
    const r = result({ metrics: [metric({ metric_id: 'direct_incident_energy_change', quantity_kind: 'direct_incident_energy', unit: 'kWh', value: -2.5 })] })
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
    expect(narrativeView('I cannot estimate cooling in °C from a shade model.', result()).needsWarning).toBe(false)
  })
})
