import type { Metric, Result, Scenario } from '../api/types'
import { diffInputs, type FieldChange } from './evaluation'

type Case = Scenario['input']['evaluation_cases'][number]

/** A metric is only comparable with another of the same meaning: id, case, target, unit, kind, horizon, area basis. */
export const metricKey = (m: Metric) =>
  [m.metric_id, m.case_id, m.target_id ?? '-', m.unit, m.quantity_kind, m.horizon_years, m.area_basis ?? '-', m.weighting].join('|')

export interface MetricPair {
  readonly key: string
  readonly label: string
  readonly base: Metric | null
  readonly alternative: Metric | null
  /** alternative − base, only when both exist with identical meaning. Computed in the UI from two stored values. */
  readonly difference: number | null
  readonly note: string | null
}

const label = (m: Metric) => `${m.metric_id.replace(/_/g, ' ')} · case ${m.case_id}${m.target_id ? ` · ${m.target_id}` : ''} · ${m.horizon_years} y`

export function pairMetrics(base: Result, alternative: Result): MetricPair[] {
  const left = new Map(base.metrics.map(m => [metricKey(m), m]))
  const right = new Map(alternative.metrics.map(m => [metricKey(m), m]))
  return [...new Set([...left.keys(), ...right.keys()])].sort().map(key => {
    const b = left.get(key) ?? null
    const a = right.get(key) ?? null
    const both = b !== null && a !== null
    return {
      key,
      label: label((b ?? a)!),
      base: b,
      alternative: a,
      difference: both ? a.value - b.value : null,
      note: both ? null : `Only in the ${b ? 'base' : 'alternative'} run; not compared.`,
    }
  })
}

export interface RunComparison {
  readonly sameScenario: boolean
  readonly changes: readonly FieldChange[]
  readonly pairs: readonly MetricPair[]
  readonly movedPlacements: readonly { readonly placementId: string; readonly from: readonly number[] | null; readonly to: readonly number[] | null }[]
  /** "controlled relocation" only when exactly one placement moved and nothing else in the inputs changed. */
  readonly kind: 'identical-inputs' | 'controlled-relocation' | 'multiple-changes'
}

/** Compare two stored runs. Changed inputs come from their own scenario snapshots, never from the current draft. */
export function compareRuns(base: { result: Result; scenario: Scenario }, alt: { result: Result; scenario: Scenario }): RunComparison {
  const changes = diffInputs(base.scenario.input, alt.scenario.input).filter(c => c.path !== 'search.deadline_utc')
  const before = new Map(base.result.layouts.flatMap(l => l.layout.placements).map(p => [p.placement_id, p.position_enu_m]))
  const after = new Map(alt.result.layouts.flatMap(l => l.layout.placements).map(p => [p.placement_id, p.position_enu_m]))
  const movedPlacements = [...new Set([...before.keys(), ...after.keys()])]
    .filter(id => JSON.stringify(before.get(id)) !== JSON.stringify(after.get(id)))
    .map(id => ({ placementId: id, from: before.get(id) ?? null, to: after.get(id) ?? null }))
  const nonLayout = changes.filter(c => !c.path.startsWith('proposed_layout_ref'))
  const kind = changes.length === 0 && movedPlacements.length === 0 ? 'identical-inputs'
    : movedPlacements.length === 1 && nonLayout.length === 0 && movedPlacements[0].from && movedPlacements[0].to ? 'controlled-relocation'
      : 'multiple-changes'
  return { sameScenario: base.result.scenario_id === alt.result.scenario_id, changes, pairs: pairMetrics(base.result, alt.result), movedPlacements, kind }
}

/** Rows for a backend comparison result (compare_locations / compare_scenarios), resolving metric instance ids. */
export function deltaRows(result: Result) {
  const byId = new Map(result.metrics.map(m => [m.metric_instance_id, m]))
  return (result.comparison?.deltas ?? []).map(d => ({
    base: byId.get(d.base_metric_instance_id) ?? null,
    alternative: byId.get(d.alternative_metric_instance_id) ?? null,
    delta: d,
    resolved: byId.has(d.base_metric_instance_id) && byId.has(d.alternative_metric_instance_id),
  }))
}

export interface TimeBinView { readonly utc: string; readonly local: string; readonly durationH: number; readonly zone: string }

/** Analysis time bins, shown in UTC and in the scenario's display time zone (labelled), never "now". */
export function timeBins(c: Case, zone: string): TimeBinView[] {
  const options = (timeZone: string): Intl.DateTimeFormatOptions => ({
    timeZone, day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZoneName: 'short',
  })
  let fmt: Intl.DateTimeFormat
  let used = zone
  try {
    fmt = new Intl.DateTimeFormat('en-GB', options(zone))
  } catch {
    used = 'UTC'
    fmt = new Intl.DateTimeFormat('en-GB', options('UTC'))
  }
  return c.time_bins.map(b => ({ utc: b.midpoint_utc, local: fmt.format(new Date(b.midpoint_utc)), durationH: b.duration_h, zone: used }))
}

export const CASE_ROLE_LABEL: Record<Case['role'], string> = {
  benefit: 'Benefit (summer shade)',
  winter_check: 'Winter check',
  establishment_report: 'Establishment report',
  sensitivity: 'Sensitivity',
}

export interface WinterView {
  readonly status: 'not-in-scenario' | 'no-result' | 'reported'
  readonly cases: readonly Case[]
  readonly limits: Scenario['input']['constraints']['winter_limits']
  readonly metrics: readonly Metric[]
  readonly constraints: Result['constraints']
  readonly missing: Result['missing_metrics']
}

/** Winter trade-off strictly from the scenario's winter cases/limits and the result's records. */
export function winterView(scenario: Scenario, result: Result | null): WinterView {
  const cases = scenario.input.evaluation_cases.filter(c => c.role === 'winter_check')
  const limits = scenario.input.constraints.winter_limits
  if (cases.length === 0 && limits.length === 0) return { status: 'not-in-scenario', cases, limits, metrics: [], constraints: [], missing: [] }
  if (!result) return { status: 'no-result', cases, limits, metrics: [], constraints: [], missing: [] }
  const ids = new Set([...cases.map(c => c.case_id), ...limits.map(l => l.case_id)])
  return {
    status: 'reported',
    cases,
    limits,
    metrics: result.metrics.filter(m => m.metric_id === 'winter_sun_loss' || ids.has(m.case_id) && m.metric_id !== 'additional_shade'),
    constraints: result.constraints.filter(c => c.case_id !== null && ids.has(c.case_id)),
    missing: result.missing_metrics.filter(m => ids.has(m.case_id) || m.metric_id === 'winter_sun_loss'),
  }
}

/** Metrics this system computes. Anything else (cooling, AQI, CO2, flood, bills) is out of scope by design. */
export const SUPPORTED_METRICS: readonly Metric['metric_id'][] = ['additional_shade', 'weighted_shade_utility', 'winter_sun_loss', 'direct_incident_energy_change']
