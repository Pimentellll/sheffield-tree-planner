import type { Health, Job, Metric, Result } from '../api/types'
import { CURRENTNESS_LABEL, EXECUTION_MODE_LABEL, formatPence, formatValue, unitLabel, type Currentness } from './evaluation'

/**
 * Presentation helpers for planning-agent evidence (#74), written BEFORE Ben's agent-run API (#73).
 *
 * Deliberately defines NO agent-run wire types (run, status or event shapes). Those come only from
 * the backend-generated contract once #73 is agreed. Everything here works on the existing,
 * authoritative Job/Result/Health types, so it stays valid whatever the agent-run surface becomes:
 *
 * - `agentPanelState`: the explicit "agent unavailable" state required while no agent API exists.
 * - `evidenceChain`: the backend-only half of model → tool → Job → Result. It mirrors the identity
 *   part of the backend's `validate_delivery_currentness`, keyed on the requesting Job's delivery
 *   (docs/CONTRACTS.md: Job delivery and execution-mode rules), so cache hits are valid.
 * - `narrativeView`: keeps model text as interpretation and flags the figures it RECOGNISES (a
 *   number with a recognised unit, scale or currency), plus any number written next to a
 *   temperature unit. It is a guard, not a proof: see `narrativeFigures` for the known gaps.
 */

// ---------------------------------------------------------------------------------------------
// Availability

export const AGENT_API_UNAVAILABLE_REASON =
  'This interface has no planning-agent integration yet, so no agent history can be shown. Nothing on this panel is a model transcript.'
const MANUAL_AVAILABLE = ' Manual evaluation is unaffected.'
const MANUAL_UNAVAILABLE = ' Manual evaluation is not offered by this backend either.'

/** Only one state exists until #73 lands; the union is extended from the generated contract, not here. */
export type AgentPanelState = {
  readonly kind: 'unavailable'
  readonly reason: string
  /** Whether the manual evaluate path the user can fall back to is offered by this backend. */
  readonly manualEvaluateAvailable: boolean
}

export function agentPanelState(health: Pick<Health, 'available_operations'> | null): AgentPanelState {
  const manualEvaluateAvailable = health?.available_operations.includes('evaluate_layout') ?? false
  return {
    kind: 'unavailable',
    reason: AGENT_API_UNAVAILABLE_REASON + (manualEvaluateAvailable ? MANUAL_AVAILABLE : MANUAL_UNAVAILABLE),
    manualEvaluateAvailable,
  }
}

// ---------------------------------------------------------------------------------------------
// Evidence chain (backend values only)

export type ChainJob = Pick<Job, 'job_id' | 'status' | 'operation' | 'scenario_id' | 'scenario_revision' | 'scope' | 'delivery'>
export type ChainResult = Pick<Result, 'run_id' | 'source_job_id' | 'input_fingerprint' | 'input_snapshot_ref' | 'operation' | 'metrics' | 'limitations'> & {
  readonly provenance: Pick<Result['provenance'], 'execution_mode'>
  readonly layouts: ReadonlyArray<Pick<Result['layouts'][number], 'cost_pence' | 'selected'>>
  readonly missing_metrics: ReadonlyArray<Pick<Result['missing_metrics'][number], 'metric_id' | 'case_id' | 'layout_id' | 'reason'>>
}

export interface EvidenceStep {
  readonly kind: 'scenario' | 'operation' | 'job' | 'result' | 'provenance' | 'currentness' | 'metric' | 'missing-metric' | 'cost' | 'limitation'
  readonly label: string
  readonly value: string
}

export type EvidenceChain =
  | { readonly ok: true; readonly currentness: Currentness; readonly steps: readonly EvidenceStep[] }
  | { readonly ok: false; readonly problems: readonly string[] }

/**
 * Why a Result cannot be shown as the answer to a Job. Empty when they are linked. Mirrors the
 * identity half of the backend's `validate_delivery_currentness` (contracts/results.py): the
 * requesting Job's `delivery` names the run, source job and fingerprint, and the Result's input
 * snapshot is the Job's scenario. A cache hit delivers an older run whose `source_job_id` is the
 * original job, NOT the requesting one, and is valid. Selection/currentness is decided separately
 * by the workspace guard and passed to `evidenceChain`.
 */
export function linkageProblems(job: ChainJob, result: ChainResult): string[] {
  const problems: string[] = []
  if (job.status !== 'completed') problems.push(`Job ${job.job_id} is ${job.status}, not completed.`)
  const d = job.delivery
  if (!d) {
    problems.push(`Job ${job.job_id} has no delivery record, so no Result can be attributed to it.`)
    return problems
  }
  if (d.job_id !== job.job_id) problems.push(`The delivery belongs to job ${d.job_id}, not ${job.job_id}.`)
  if (result.run_id !== d.run_id) problems.push(`Job ${job.job_id} delivered run ${d.run_id}, not ${result.run_id}.`)
  if (result.source_job_id !== d.source_job_id) problems.push(`Result ${result.run_id} was produced by job ${result.source_job_id}; the delivery names ${d.source_job_id}.`)
  if (result.input_fingerprint !== d.input_fingerprint) problems.push(`Result ${result.run_id} input fingerprint differs from the delivery for job ${job.job_id}.`)
  const ref = result.input_snapshot_ref
  if (ref.scenario_id !== job.scenario_id || ref.revision !== job.scenario_revision || ref.scope !== job.scope) {
    problems.push(`Result ${result.run_id} was computed from a different scenario revision than job ${job.job_id} requested.`)
  }
  if (result.operation !== job.operation) problems.push(`Result operation ${result.operation} differs from job operation ${job.operation}.`)
  return problems
}

/**
 * Distinguishes rows that share a metric and case: the physical runtime emits an aggregate row
 * (target_id null) plus one row per target, per case and layout.
 */
export function metricLabel(m: Pick<Metric, 'metric_id' | 'case_id' | 'target_id' | 'layout_id' | 'quantity_kind'>): string {
  return `${m.metric_id} · case ${m.case_id} · ${m.target_id ?? 'all targets'} · layout ${m.layout_id} · ${m.quantity_kind}`
}

/** A metric value in its unit. Money is converted from integer pence exactly once, here. */
export function metricText(metric: Pick<Metric, 'value' | 'unit'>): string {
  if (metric.unit === 'GBP_pence') return Number.isSafeInteger(metric.value) ? formatPence(metric.value) : `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
  return `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
}

/**
 * The backend-only evidence chain for one Job and its Result. `currentness` must come from the
 * workspace's existing guard (`Workspace.currentness`), so this never decides CURRENT on its own.
 * Returns problems instead of steps when the Result does not belong to the Job; the caller must
 * then show nothing from the Result.
 */
export function evidenceChain(job: ChainJob, result: ChainResult, currentness: Currentness): EvidenceChain {
  const problems = linkageProblems(job, result)
  if (problems.length || !job.delivery) return { ok: false, problems }
  const d = job.delivery
  const steps: EvidenceStep[] = [
    { kind: 'scenario', label: 'Scenario', value: `${job.scope} ${job.scenario_id} revision ${job.scenario_revision}` },
    { kind: 'operation', label: 'Operation', value: result.operation },
    { kind: 'job', label: 'Job', value: job.job_id },
    // Current mode comes from the delivery: a cache hit must not look live (CONTRACTS.md).
    { kind: 'result', label: 'Result', value: `${result.run_id} · delivered as: ${EXECUTION_MODE_LABEL[d.execution_mode]}` },
    { kind: 'provenance', label: 'Original computation', value: `job ${result.source_job_id} · ${EXECUTION_MODE_LABEL[result.provenance.execution_mode]}` },
    { kind: 'currentness', label: 'Status', value: CURRENTNESS_LABEL[currentness].label },
    ...result.metrics.map((m): EvidenceStep => ({ kind: 'metric', label: metricLabel(m), value: metricText(m) })),
    ...result.missing_metrics.map((m): EvidenceStep => ({ kind: 'missing-metric', label: `${m.metric_id} · case ${m.case_id} · layout ${m.layout_id}`, value: `Not computed: ${m.reason}` })),
    ...result.layouts.filter(l => l.selected).map((l): EvidenceStep => ({ kind: 'cost', label: 'Cost of selected layout', value: formatPence(l.cost_pence) })),
    ...result.limitations.map((text): EvidenceStep => ({ kind: 'limitation', label: 'Limitation', value: text })),
  ]
  return { ok: true, currentness, steps }
}

// ---------------------------------------------------------------------------------------------
// Untrusted model narrative

export const MODEL_INTERPRETATION_LABEL = 'Model interpretation, not a computed result'

export type FigureKind =
  | 'temperature' | 'percent' | 'money' | 'shade_m2_h' | 'weighted_shade' | 'energy_kWh' | 'energy_kWh_per_m2' | 'area_m2' | 'hours' | 'length_m'
  | 'unknown' // a quantity whose unit or scale this guard cannot attribute (angles, "2 K", foreign currency)

/**
 * - `unsupported`: no registered operation computes this kind of quantity (°C, %).
 * - `unverified`: computable or unattributable, and equal to no value in the given Result.
 * - `appears-in-result`: equals (to the precision written, sign included) SOME value of that unit in
 *   the given Result: any case, any layout, including non-selected or infeasible ones. It does not
 *   prove the model attached it to the right case or layout; it is still model text, and the
 *   authoritative number is the metric card, never the narrative.
 */
export type FigureStatus = 'unsupported' | 'unverified' | 'appears-in-result'

export interface NarrativeFigure {
  readonly text: string
  readonly index: number
  readonly kind: FigureKind
  readonly status: FigureStatus
}

export interface NarrativeView {
  readonly label: typeof MODEL_INTERPRETATION_LABEL
  readonly text: string
  readonly figures: readonly NarrativeFigure[]
  /** A number is written next to a temperature unit, even in a form `figures` cannot parse ("12,3 °C", ".5 °C"). */
  readonly temperatureMentioned: boolean
  /** True when a recognised figure is not traceable to the given Result, or a temperature is stated. The UI should warn calmly: benign text ("3 m apart", "45°") also triggers it. */
  readonly needsWarning: boolean
}

type NarrativeEvidence = Pick<ChainResult, 'metrics' | 'layouts'>

// A number not glued to a preceding word, digit or decimal point ("C5", "v1.2" and the "12" of
// "10-12" do not start a negative or a new figure). The minus sign is only a sign after a non-word.
const NUMBER = String.raw`(?:(?<![\w.,])[-−])?(?<![\w.,])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?`
// Scale words. A lone "m" is a scale only when not followed by ²/2/·/_ or a letter (so "m²" stays a unit).
const SCALE = String.raw`k(?!\w)|bn(?!\w)|mn(?!\w)|tn(?!\w)|m(?![²2·_\w])|thousands?\b|millions?\b|billions?\b|trillions?\b`
const UNIT = [
  String.raw`weighted\s+m(?:²|2)(?:·|_|\s)?h\b`,
  String.raw`kWh\s?(?:\/|per\s)\s?m(?:²|2)`,
  String.raw`kWh\b`,
  String.raw`°\s?[CF](?:elsius|ahrenheit)?\b`, String.raw`º\s?[CF]\b`, '[℃℉]',
  String.raw`deg(?:rees?)?\s?(?:celsius|fahrenheit|C|F)\b`, String.raw`kelvin\b`,
  String.raw`degrees?\b`, '°',
  String.raw`per\s?cent(?:age\s+points?)?\b`, String.raw`percentage\s+points?\b`, '%',
  String.raw`m(?:²|2)(?:·|_|\s)?h\b`, String.raw`square[- ]met(?:re|er)[- ]hours?\b`,
  'm²', String.raw`m2\b`, String.raw`square\s+met(?:re|er)s?\b`,
  String.raw`hours?\b`, String.raw`hrs?\b`, String.raw`h\b`,
  String.raw`met(?:re|er)s?\b`,
  String.raw`pounds?\b`, String.raw`GBP\b`, String.raw`pence\b`, String.raw`p(?=[\s,;:)!?]|$|\.(?:\s|$))`,
].join('|')
// An optional sign may precede the currency symbol ("−£450"); a scale may be hyphenated ("£450-million").
const FIGURE = new RegExp(String.raw`([-−]?[£$€]\s?)?(${NUMBER})(?:\s?-?\s?(${SCALE}))?\s?(${UNIT})?`, 'gi')

const TEMPERATURE = /^(?:°\s?[cf]|º|℃|℉|deg(?:rees?)?\s?(?:c|f|celsius|fahrenheit)$|kelvin)/
/** Any digit next to a temperature unit, as a backstop for forms the figure parser skips. */
const TEMPERATURE_NEAR_NUMBER = /\d\s?(?:°\s?[CF]|º\s?[CF]|[℃℉]|deg(?:rees?)?\s?(?:celsius|fahrenheit|C|F)\b|kelvin\b)/i
const SHADE = /^(?:m(?:²|2)(?:·|_| )?h|square[- ]met(?:re|er)[- ]hours?)$/
const METRIC_UNIT: Partial<Record<FigureKind, Metric['unit']>> = {
  shade_m2_h: 'm2_h', weighted_shade: 'weighted_m2_h', energy_kWh: 'kWh', energy_kWh_per_m2: 'kWh_per_m2', area_m2: 'm2', hours: 'h', length_m: 'm',
}

const decimals = (numberText: string) => numberText.split('.')[1]?.length ?? 0
const parseNumber = (numberText: string) => Number(numberText.replace(/−/g, '-').replace(/,/g, ''))
/** Half a unit in the last written decimal place: "12.3" may round any value in [12.25, 12.35]. */
const writtenTolerance = (numberText: string) => 0.5 * 10 ** -decimals(numberText)

interface Classified { readonly kind: FigureKind; readonly money?: 'pounds' | 'pence' | 'foreign'; readonly multiplier: number; readonly negative?: boolean }

function multiplierOf(scale: string): number {
  const s = scale.length > 2 ? scale.replace(/s$/, '') : scale // plural words only ("millions")
  if (s === 'k' || s === 'thousand') return 1e3
  if (s === 'm' || s === 'mn' || s === 'million') return 1e6
  if (s === 'bn' || s === 'billion') return 1e9
  if (s === 'tn' || s === 'trillion') return 1e12
  return 1
}

function classify(currency: string, scaleText: string, unitText: string): Classified | null {
  const s = scaleText.toLowerCase()
  const u = unitText.toLowerCase().replace(/\s+/g, ' ')
  const multiplier = multiplierOf(s)
  if (currency) {
    const negative = currency.startsWith('-') || currency.startsWith('−')
    return { kind: 'money', money: currency.endsWith('£') ? 'pounds' : 'foreign', multiplier, negative }
  }
  if (u.startsWith('pound') || u === 'gbp') return { kind: 'money', money: 'pounds', multiplier }
  if (u === 'pence' || u === 'p') return { kind: 'money', money: 'pence', multiplier }
  // Without a currency, a lone trailing "m" is metres ("4.2 m"); any other lone scale is unattributable.
  if (!u && s) return s === 'm' ? { kind: 'length_m', multiplier: 1 } : { kind: 'unknown', multiplier: 1 }
  if (!u) return null
  if (u.startsWith('weighted')) return { kind: 'weighted_shade', multiplier }
  if (u.startsWith('kwh')) return { kind: u === 'kwh' ? 'energy_kWh' : 'energy_kWh_per_m2', multiplier }
  if (TEMPERATURE.test(u)) return { kind: 'temperature', multiplier }
  if (u === '°' || u.startsWith('degree')) return { kind: 'unknown', multiplier } // an angle, or an unstated scale
  if (u === '%' || u.startsWith('per')) return { kind: 'percent', multiplier }
  if (SHADE.test(u)) return { kind: 'shade_m2_h', multiplier }
  if (u === 'm²' || u === 'm2' || u.startsWith('square')) return { kind: 'area_m2', multiplier }
  if (/^(?:h|hrs?|hours?)$/.test(u)) return { kind: 'hours', multiplier }
  if (/^met(?:re|er)s?$/.test(u)) return { kind: 'length_m', multiplier }
  return { kind: 'unknown', multiplier }
}

const near = (a: number, b: number, tolerance: number) => Math.abs(a - b) <= tolerance + 1e-9

function statusOf(c: Classified, value: number, tolerance: number, evidence: NarrativeEvidence | null): FigureStatus {
  // No registered operation computes air/surface temperature or a percentage.
  if (c.kind === 'temperature' || c.kind === 'percent') return 'unsupported'
  if (c.kind === 'unknown' || c.money === 'foreign' || !evidence) return 'unverified'
  const scaled = value * c.multiplier
  const scaledTolerance = tolerance * c.multiplier
  if (c.kind === 'money') {
    const toPence = c.money === 'pence' ? 1 : 100
    const candidates = [...evidence.layouts.map(l => l.cost_pence), ...evidence.metrics.filter(m => m.unit === 'GBP_pence').map(m => m.value)]
    return candidates.some(p => near(scaled * toPence, p, scaledTolerance * toPence)) ? 'appears-in-result' : 'unverified'
  }
  const unit = METRIC_UNIT[c.kind]
  return evidence.metrics.some(m => m.unit === unit && near(scaled, m.value, scaledTolerance)) ? 'appears-in-result' : 'unverified'
}

/**
 * A figure guard, not a claim filter. It finds numbers written with a RECOGNISED unit, scale or
 * currency in model text and says whether the given Result contains that value. Known gaps, which
 * are not flagged here: units it does not list ("1.2 MWh", "0.5 kW", "3 km", "300 kg", "5 pct",
 * "450 dollars"); numbers written after their unit ("Additional shade (m²·h): 99.9"); numbers
 * glued to a preceding ".", "," or "_" ("12,3", ".5"); and spelled-out or qualitative claims
 * ("two degrees", "noticeably cooler"). `narrativeView` adds a temperature backstop for the
 * glued forms. Bare counts and identifiers ("3 trees", "revision 2", "C5") are left alone. Signs
 * are compared strictly, so "reduces by 2.5 kWh" against a stored -2.5 is unverified (noisy but
 * safe). Pass `null` evidence when no validated Result is attached.
 */
export function narrativeFigures(text: string, evidence: NarrativeEvidence | null): NarrativeFigure[] {
  const figures: NarrativeFigure[] = []
  for (const match of text.matchAll(FIGURE)) {
    const [whole, currency, numberText, scale, unit] = match
    const c = classify((currency ?? '').trim(), scale ?? '', unit ?? '')
    if (!c) continue
    const parsed = parseNumber(numberText)
    const value = c.negative ? -parsed : parsed
    if (!Number.isFinite(value)) continue
    figures.push({ text: whole.trim(), index: match.index ?? 0, kind: c.kind, status: statusOf(c, value, writtenTolerance(numberText), evidence) })
  }
  return figures
}

/** Model prose packaged for display as interpretation, with its figures checked against the Result. */
export function narrativeView(text: string, evidence: NarrativeEvidence | null): NarrativeView {
  const figures = narrativeFigures(text, evidence)
  const temperatureMentioned = TEMPERATURE_NEAR_NUMBER.test(text)
  return {
    label: MODEL_INTERPRETATION_LABEL, text, figures, temperatureMentioned,
    needsWarning: temperatureMentioned || figures.some(f => f.status !== 'appears-in-result'),
  }
}
