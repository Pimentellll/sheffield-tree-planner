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
  it('flags unsupported and unverified figures, and recognises ones that match the result', () => {
    const text = 'Planting here adds 12.3 m²·h of shade for £450.00, cooling the street by 3 °C and saving £1,200 a year (40% more shade).'
    expect(narrativeFigures(text, result()).map(f => [f.text, f.kind, f.status])).toEqual([
      ['12.3 m²·h', 'shade_m2_h', 'matches-result'],
      ['£450.00', 'money', 'matches-result'],
      ['3 °C', 'temperature', 'unsupported'],
      ['£1,200', 'money', 'unverified'],
      ['40%', 'percent', 'unsupported'],
    ])
  })
  it('leaves bare counts and identifiers alone', () => {
    expect(narrativeFigures('Revision 2 has 3 trees in case C5.', result())).toEqual([])
  })
  it('treats every computable figure as unverified when no validated result is attached', () => {
    expect(narrativeFigures('adds 12.3 m²·h, about 3 °C cooler', null).map(f => f.status)).toEqual(['unverified', 'unsupported'])
  })
  it('matches only to the precision the model wrote', () => {
    const statuses = (text: string) => narrativeFigures(text, result()).map(f => f.status)
    expect(statuses('12 m²·h')).toEqual(['matches-result'])
    expect(statuses('12.30 m²·h')).toEqual(['unverified'])
    expect(statuses('£450')).toEqual(['matches-result'])
    expect(statuses('£451')).toEqual(['unverified'])
    expect(statuses('45000 pence')).toEqual(['matches-result'])
  })
  it('reads unicode minus signs and energy units', () => {
    const r = result({ metrics: [metric({ metric_id: 'direct_incident_energy_change', quantity_kind: 'direct_incident_energy', unit: 'kWh', value: -2.5 })] })
    expect(narrativeFigures('changes incident energy by −2.5 kWh', r).map(f => [f.kind, f.status])).toEqual([['energy_kWh', 'matches-result']])
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
