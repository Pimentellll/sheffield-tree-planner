import type { Health, Job, Metric, Result, ScenarioRef } from '../api/types'
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
 *   (docs/CONTRACTS.md: Job delivery and execution-mode rules), so cache hits are valid, and it
 *   always shows the Result's analytical outcome and every evaluated layout's cost and reasons.
 * - `narrativeView`: keeps model text as interpretation and flags the figures it RECOGNISES (a
 *   number with a recognised unit, scale or currency), plus any number written next to a
 *   temperature unit. It is a guard, not a proof: see `narrativeFigures` for the known gaps.
 *
 * Currentness is an INPUT (`Workspace.currentness`, built on evaluation.ts `classifyResult`). That
 * guard compares a Result with the accepted head, so it has no source of truth for results of a
 * hypothetical scenario (they always read as SUPERSEDED). Fixing that needs a decision with the
 * #73 contract on how hypothetical/proposal results are selected; nothing here decides CURRENT.
 */

// ---------------------------------------------------------------------------------------------
// Availability

export const AGENT_API_UNAVAILABLE_REASON =
  'This interface has no planning-agent integration yet, so no agent history can be shown. Nothing on this panel is a model transcript.'
const MANUAL_AVAILABLE = ' Manual evaluation is unaffected.'
const MANUAL_UNAVAILABLE = ' Manual evaluation is not offered by this backend either.'
const WORKER_MANUAL = ' The job worker is in manual mode, so a submitted evaluation waits until a worker is run.'

/** Only one state exists until #73 lands; the union is extended from the generated contract, not here. */
export type AgentPanelState = {
  readonly kind: 'unavailable'
  readonly reason: string
  /** Whether the manual evaluate path the user can fall back to is offered by this backend. */
  readonly manualEvaluateAvailable: boolean
  /** From `/api/v1/health` `worker_mode`: true for "background", false for "manual", null when unknown. */
  readonly workerRunning: boolean | null
}

/**
 * `/api/v1/health` is an untyped dict on the backend, so every field is read defensively: a
 * missing or malformed `available_operations` means "not offered", never a crash.
 */
export function agentPanelState(health: Partial<Pick<Health, 'available_operations' | 'worker_mode'>> | null | undefined): AgentPanelState {
  const rawOperations: unknown = health?.available_operations
  const operations: readonly unknown[] = Array.isArray(rawOperations) ? rawOperations : []
  const manualEvaluateAvailable = operations.includes('evaluate_layout')
  const rawMode: unknown = health?.worker_mode
  const mode = typeof rawMode === 'string' ? rawMode : null
  const workerRunning = mode === 'background' ? true : mode === 'manual' ? false : null
  return {
    kind: 'unavailable',
    reason: AGENT_API_UNAVAILABLE_REASON + (manualEvaluateAvailable ? MANUAL_AVAILABLE : MANUAL_UNAVAILABLE) +
      (manualEvaluateAvailable && workerRunning === false ? WORKER_MANUAL : ''),
    manualEvaluateAvailable,
    workerRunning,
  }
}

// ---------------------------------------------------------------------------------------------
// Evidence chain (backend values only)

type EvaluatedLayout = Result['layouts'][number]
export type ChainLayout = Pick<EvaluatedLayout, 'cost_pence' | 'selected' | 'role' | 'feasibility' | 'reasons' | 'scenario_ref'> & {
  readonly layout: Pick<EvaluatedLayout['layout'], 'layout_id'>
}
export type ChainJob = Pick<Job, 'job_id' | 'status' | 'operation' | 'scenario_id' | 'scenario_revision' | 'scope' | 'delivery'>
export type ChainResult = Pick<Result, 'run_id' | 'source_job_id' | 'input_fingerprint' | 'input_snapshot_ref' | 'operation' | 'analytical_outcome' | 'metrics' | 'limitations'> & {
  readonly provenance: Pick<Result['provenance'], 'execution_mode'>
  readonly layouts: ReadonlyArray<ChainLayout>
  readonly missing_metrics: ReadonlyArray<Pick<Result['missing_metrics'][number], 'metric_id' | 'case_id' | 'layout_id' | 'reason' | 'scenario_ref'>>
}

export interface EvidenceStep {
  readonly kind: 'scenario' | 'operation' | 'outcome' | 'job' | 'result' | 'provenance' | 'currentness' | 'metric' | 'missing-metric' | 'cost' | 'limitation'
  readonly label: string
  readonly value: string
}

/**
 * Wording for each backend analytical outcome. `feasible` is true only for the two outcomes the
 * backend allows to select a recommendation and false for the three unsuccessful outcomes. For
 * `comparison_completed` (evaluate_layout and the compare operations) it is null here and is
 * derived from the layouts by `evidenceChain`.
 */
export const ANALYTICAL_OUTCOME_LABEL: Record<Result['analytical_outcome'], { readonly label: string; readonly feasible: boolean | null }> = {
  comparison_completed: { label: 'Computed (feasibility shown per layout)', feasible: null },
  feasible_candidate: { label: 'Feasible planting layout found', feasible: true },
  feasible_zero_planting: { label: 'Feasible only with zero planting', feasible: true },
  no_eligible_candidates: { label: 'No eligible candidate positions', feasible: false },
  search_exhausted_without_target: { label: 'Search exhausted without reaching the target', feasible: false },
  proven_infeasible_finite_model: { label: 'Proven infeasible within the finite model', feasible: false },
}

export type EvidenceChain =
  | {
    readonly ok: true
    readonly currentness: Currentness
    readonly outcome: Result['analytical_outcome']
    /**
     * False means the computed result is NOT a feasible planting outcome; it is still valid
     * evidence. For `comparison_completed` it comes from the proposed ("alternative") layouts, or
     * all layouts if none has that role: false if every one is infeasible, true if every one is
     * feasible, otherwise null (mixed, or not evaluated).
     */
    readonly feasible: boolean | null
    readonly steps: readonly EvidenceStep[]
  }
  | { readonly ok: false; readonly problems: readonly string[] }

/**
 * Why a Result cannot be shown as the answer to a Job. Empty when they are linked. Mirrors the
 * identity half of the backend's `validate_delivery_currentness` (contracts/results.py): the
 * requesting Job's `delivery` names the run, source job and fingerprint, and the Result's input
 * snapshot is the Job's scenario. A cache hit delivers an older run whose `source_job_id` is the
 * original job, NOT the requesting one, and is valid. A delivery that claims to be `live` must
 * carry a live computation by this very job (CONTRACTS.md: a cache hit cannot look live).
 * Selection/currentness is decided separately by the workspace guard and passed to `evidenceChain`.
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
  // Latent coupling: the backend stamps every fresh delivery "live" regardless of the Result's provenance
  // (jobs/__init__.py ~682; only cache hits are "cached", ~784), so a future recorded/fixture evaluator would be refused here.
  if (d.execution_mode === 'live' && (result.provenance.execution_mode !== 'live' || d.source_job_id !== job.job_id)) {
    problems.push(`The delivery for job ${job.job_id} says live, but Result ${result.run_id} is a ${result.provenance.execution_mode} computation by job ${d.source_job_id}.`)
  }
  return problems
}

/** Integer pence as pounds, converted once. A non-integer or negative amount is shown raw and marked, never rounded into a price. */
function penceText(pence: number): string {
  return Number.isSafeInteger(pence) && pence >= 0 ? formatPence(pence) : `${formatValue(pence)} GBP pence (not a valid whole amount)`
}

/** A metric value in its unit. Money is converted from integer pence exactly once, here. */
export function metricText(metric: Pick<Metric, 'value' | 'unit'>): string {
  if (metric.unit === 'GBP_pence') return Number.isSafeInteger(metric.value) ? formatPence(metric.value) : `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
  return `${formatValue(metric.value)} ${unitLabel(metric.unit)}`
}

const refText = (r: ScenarioRef) => `${r.scope} ${r.scenario_id} r${r.revision}`

/**
 * Distinguishes rows that share a metric and case: the physical runtime emits an aggregate row
 * (target_id null) plus one row per target, per case and layout. With `withScenario` (set by
 * `evidenceChain` when a Result spans several scenarios, as compare_scenarios does) the scenario
 * is added too.
 */
export function metricLabel(
  m: Pick<Metric, 'metric_id' | 'case_id' | 'target_id' | 'layout_id' | 'quantity_kind'> & { readonly scenario_ref?: ScenarioRef },
  withScenario = false,
): string {
  const base = `${m.metric_id} · case ${m.case_id} · ${m.target_id ?? 'all targets'} · layout ${m.layout_id} · ${m.quantity_kind}`
  return withScenario && m.scenario_ref ? `${base} · ${refText(m.scenario_ref)}` : base
}

function chainFeasibility(result: ChainResult): boolean | null {
  const fixed = ANALYTICAL_OUTCOME_LABEL[result.analytical_outcome].feasible
  if (fixed !== null || result.analytical_outcome !== 'comparison_completed') return fixed
  const proposed = result.layouts.filter(l => l.role === 'alternative')
  const pool = proposed.length ? proposed : result.layouts
  if (!pool.length) return null
  if (pool.every(l => l.feasibility === 'infeasible')) return false
  if (pool.every(l => l.feasibility === 'feasible')) return true
  return null
}

/**
 * The backend-only evidence chain for one Job and its Result. `currentness` must come from the
 * workspace's existing guard (`Workspace.currentness`), so this never decides CURRENT on its own.
 * Returns problems instead of steps when the Result does not belong to the Job; the caller must
 * then show nothing from the Result. Every evaluated layout's cost is shown with its role,
 * feasibility and (for non-feasible layouts) the backend's reasons: `evaluate_layout` and the
 * compare operations select no layout (contracts/results.py lets only the two feasible search
 * outcomes select one).
 */
export function evidenceChain(job: ChainJob, result: ChainResult, currentness: Currentness): EvidenceChain {
  const problems = linkageProblems(job, result)
  if (problems.length || !job.delivery) return { ok: false, problems }
  const d = job.delivery
  const refs = new Set([...result.metrics, ...result.missing_metrics, ...result.layouts].map(x => refText(x.scenario_ref)))
  const multiScenario = refs.size > 1
  const scenarioSuffix = (r: ScenarioRef) => (multiScenario ? ` · ${refText(r)}` : '')
  const steps: EvidenceStep[] = [
    { kind: 'scenario', label: 'Scenario', value: `${job.scope} ${job.scenario_id} revision ${job.scenario_revision}` },
    { kind: 'operation', label: 'Operation', value: result.operation },
    { kind: 'outcome', label: 'Outcome', value: ANALYTICAL_OUTCOME_LABEL[result.analytical_outcome].label },
    { kind: 'job', label: 'Job', value: job.job_id },
    // Current mode comes from the delivery: a cache hit must not look live (CONTRACTS.md).
    { kind: 'result', label: 'Result', value: `${result.run_id} · delivered as: ${EXECUTION_MODE_LABEL[d.execution_mode]}` },
    { kind: 'provenance', label: 'Original computation', value: `job ${result.source_job_id} · ${EXECUTION_MODE_LABEL[result.provenance.execution_mode]}` },
    { kind: 'currentness', label: 'Status', value: CURRENTNESS_LABEL[currentness].label },
    ...result.metrics.map((m): EvidenceStep => ({ kind: 'metric', label: metricLabel(m, multiScenario), value: metricText(m) })),
    ...result.missing_metrics.map((m): EvidenceStep => ({
      kind: 'missing-metric', label: `${m.metric_id} · case ${m.case_id} · layout ${m.layout_id}${scenarioSuffix(m.scenario_ref)}`, value: `Not computed: ${m.reason}`,
    })),
    ...result.layouts.map((l): EvidenceStep => ({
      kind: 'cost',
      label: `Cost · ${l.role} layout ${l.layout.layout_id}${scenarioSuffix(l.scenario_ref)}`,
      value: `${penceText(l.cost_pence)} · ${l.feasibility.replace(/_/g, ' ')}${l.selected ? ' · selected' : ''}` +
        (l.feasibility !== 'feasible' && l.reasons.length ? ` · ${l.reasons.join('; ')}` : ''),
    })),
    ...result.limitations.map((text): EvidenceStep => ({ kind: 'limitation', label: 'Limitation', value: text })),
  ]
  return { ok: true, currentness, outcome: result.analytical_outcome, feasible: chainFeasibility(result), steps }
}

// ---------------------------------------------------------------------------------------------
// Untrusted model narrative

export const MODEL_INTERPRETATION_LABEL = 'Model interpretation, not a computed result'

export type FigureKind =
  | 'temperature' | 'percent' | 'money' | 'shade_m2_h' | 'weighted_shade' | 'energy_kWh' | 'energy_kWh_per_m2' | 'area_m2' | 'hours' | 'length_m'
  | 'degrees' // "30 degrees", "2-degree", "2 deg", "45°": an angle OR an unstated temperature, so it warns
  | 'count_scale' // a spelled scale word with no unit or currency ("10 thousand trees"): context
  | 'unknown' // a scale with no unit or currency ("450k", "1.2m", "2 K", "1.2 bn"): money, kelvin or thousands, so it warns

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
  /** The figure as written, with markdown emphasis and repeated spaces normalised. */
  readonly text: string
  readonly index: number
  readonly kind: FigureKind
  readonly status: FigureStatus
  /**
   * Only spelled counts ("10 thousand trees"). Still listed as `unverified`, but they do not by
   * themselves set `needsWarning`. Hours, lengths and areas DO warn: a misstated sample window,
   * distance or a shade figure mis-written in m² is exactly what the guard is for.
   */
  readonly contextOnly: boolean
}

export interface NarrativeView {
  readonly label: typeof MODEL_INTERPRETATION_LABEL
  readonly text: string
  readonly figures: readonly NarrativeFigure[]
  /** A number is written next to a temperature unit, even in a form `figures` cannot parse. */
  readonly temperatureMentioned: boolean
  /**
   * True when a non-context figure is not traceable to the given Result, or a temperature is
   * stated. The UI should warn calmly: it is a prompt to check, not a finding of error.
   */
  readonly needsWarning: boolean
}

type NarrativeEvidence = Pick<ChainResult, 'metrics' | 'layouts'>

const SIGN = '[-−–]'
// A number not glued to a preceding word, digit or decimal point ("C5", "v1.2" and the "12" of
// "10-12" do not start a negative or a new figure). The sign is only a sign after a non-word.
// "1,200" is thousands; "1,5" / "12,25" (one or two digits) is a decimal comma.
const NUMBER = String.raw`(?:(?<![\w.,])${SIGN})?(?<![\w.,])(?:\d{1,3}(?:,\d{3})+(?!\d)|\d+,\d{1,2}(?![\d,])|\d+)(?:\.\d+)?`
// A sign before a currency symbol counts only after a non-word, non-currency character, so the
// second figure of "£400-£450" stays positive.
const CURRENCY = String.raw`(?:(?<![\w.,£$€])${SIGN})?[£$€]`
// Scale words. A lone "m" is a scale only when not followed by ²/2/^/·/_ or a letter (so "m²" stays a unit).
const SCALE = String.raw`k(?!\w)|bn(?!\w)|mn(?!\w)|tn(?!\w)|m(?![²2^·_\w])|thousands?\b|millions?\b|billions?\b|trillions?\b`
const UNIT = [
  String.raw`weighted\s+m(?:²|2|\^2)(?:·|_|\s)?h\b`,
  String.raw`kWh\s?(?:\/|per\s)\s?m(?:²|2|\^2)`,
  String.raw`kWh\b`,
  String.raw`°\s?[CF](?:elsius|ahrenheit)?\b`, String.raw`º\s?[CF]\b`, '[℃℉]',
  String.raw`deg(?:rees?)?\s?(?:celsius|fahrenheit|C|F)\b`, String.raw`kelvin\b`, String.raw`celsius\b`, String.raw`fahrenheit\b`,
  String.raw`(?<=\d)[CF]\b`, // "3C" written directly after the digits
  String.raw`degrees?\b`, String.raw`deg\b`, '°',
  String.raw`per\s?cent(?:age\s+points?)?\b`, String.raw`percentage\s+points?\b`, '%',
  String.raw`m(?:²|2|\^2)(?:·|_|\s)?h\b`, String.raw`square[- ]met(?:re|er)[- ]hours?\b`,
  'm²', String.raw`m\^2`, String.raw`m2\b`, String.raw`square\s+met(?:re|er)s?\b`,
  String.raw`hours?\b`, String.raw`hrs?\b`, String.raw`h\b`,
  String.raw`met(?:re|er)s?\b`,
  String.raw`pounds?\b`, String.raw`GBP\b`, String.raw`pence\b`, String.raw`p(?=[\s,;:)!?]|$|\.(?:\s|$))`,
].join('|')
// Up to three spaces, or one hyphen, may separate number, scale and unit ("2-degree", "£450-million",
// and markdown emphasis, which is blanked to spaces before matching).
const SEP = String.raw`(?:\s{0,3}-?\s{0,3})`
// Separators belong to the optional scale/unit groups, so a figure never ends in a stray "-" or space.
const FIGURE = new RegExp(String.raw`(${CURRENCY}\s?)?(${NUMBER})(?:${SEP}(${SCALE}))?(?:${SEP}(${UNIT}))?`, 'gi')

const TEMPERATURE = /^(?:°\s?[cf]|º|℃|℉|deg(?:rees?)?\s?(?:c|f|celsius|fahrenheit)$|kelvin$|celsius$|fahrenheit$|[cf]$)/
/** Any digit next to a temperature unit, as a backstop for forms the figure parser skips. */
const TEMPERATURE_NEAR_NUMBER = /\d[\s*`-]{0,4}(?:°\s?[CF]|º\s?[CF]|[℃℉]|deg(?:rees?)?\s?(?:celsius|fahrenheit|C|F)\b|celsius\b|fahrenheit\b|kelvin\b)|\d[CF]\b/i
const SHADE = /^(?:m(?:²|2|\^2)(?:·|_| )?h|square[- ]met(?:re|er)[- ]hours?)$/
const METRIC_UNIT: Partial<Record<FigureKind, Metric['unit']>> = {
  shade_m2_h: 'm2_h', weighted_shade: 'weighted_m2_h', energy_kWh: 'kWh', energy_kWh_per_m2: 'kWh_per_m2', area_m2: 'm2', hours: 'h', length_m: 'm',
}
const CONTEXT_ONLY: ReadonlySet<FigureKind> = new Set<FigureKind>(['count_scale'])
/** A figure written with a scale word may round only this far, whatever its written precision ("£1m" is not £600k). */
const SCALED_RELATIVE_TOLERANCE = 0.05

/** "m**2" becomes "m^2 " (same length), then markdown emphasis/code marks become spaces, so indices stay valid. */
const normalise = (text: string) => text.replace(/m\*\*2/gi, m => `${m[0]}^2 `).replace(/[*`]/g, ' ')
const isDecimalComma = (numberText: string) => /^\D?\d+,\d{1,2}$/.test(numberText)
const decimals = (numberText: string) => (isDecimalComma(numberText) ? numberText.split(',')[1].length : (numberText.split('.')[1]?.length ?? 0))
function parseNumber(numberText: string): number {
  const signed = numberText.replace(/[−–]/g, '-')
  return Number(isDecimalComma(numberText) ? signed.replace(',', '.') : signed.replace(/,/g, ''))
}
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

function classify(currency: string, scaleText: string, unitText: string, gluedScale: boolean): Classified | null {
  const s = scaleText.toLowerCase()
  const u = unitText.toLowerCase().replace(/\s+/g, ' ')
  const multiplier = multiplierOf(s)
  if (currency) {
    const negative = /^[-−–]/.test(currency)
    return { kind: 'money', money: currency.endsWith('£') ? 'pounds' : 'foreign', multiplier, negative }
  }
  if (u.startsWith('pound') || u === 'gbp') return { kind: 'money', money: 'pounds', multiplier }
  if (u === 'pence' || u === 'p') return { kind: 'money', money: 'pence', multiplier }
  // Without a currency or unit: a spaced lone "m" is metres ("4.2 m"); a spelled word is a count
  // ("10 thousand trees"); anything else ("1.2m", "450k", "2 K", "1.2 bn") may be money, kelvin or
  // thousands and warns as unknown.
  if (!u && s) {
    if (s === 'm' && !gluedScale) return { kind: 'length_m', multiplier: 1 }
    if (s.length > 2) return { kind: 'count_scale', multiplier }
    return { kind: 'unknown', multiplier }
  }
  if (!u) return null
  if (u.startsWith('weighted')) return { kind: 'weighted_shade', multiplier }
  if (u.startsWith('kwh')) return { kind: u === 'kwh' ? 'energy_kWh' : 'energy_kWh_per_m2', multiplier }
  if (TEMPERATURE.test(u)) return { kind: 'temperature', multiplier }
  if (u === '°' || u === 'deg' || u.startsWith('degree')) return { kind: 'degrees', multiplier } // angle or unstated temperature
  if (u === '%' || u.startsWith('per')) return { kind: 'percent', multiplier }
  if (SHADE.test(u)) return { kind: 'shade_m2_h', multiplier }
  if (u === 'm²' || u === 'm^2' || u === 'm2' || u.startsWith('square')) return { kind: 'area_m2', multiplier }
  if (/^(?:h|hrs?|hours?)$/.test(u)) return { kind: 'hours', multiplier }
  if (/^met(?:re|er)s?$/.test(u)) return { kind: 'length_m', multiplier }
  return { kind: 'unknown', multiplier }
}

const near = (a: number, b: number, tolerance: number) => Math.abs(a - b) <= tolerance + 1e-9

function statusOf(c: Classified, value: number, tolerance: number, evidence: NarrativeEvidence | null): FigureStatus {
  // No registered operation computes air/surface temperature or a percentage.
  if (c.kind === 'temperature' || c.kind === 'percent') return 'unsupported'
  if (c.kind === 'unknown' || c.kind === 'degrees' || c.kind === 'count_scale' || c.money === 'foreign' || !evidence) return 'unverified'
  const scaled = value * c.multiplier
  const scaledTolerance = c.multiplier > 1 ? Math.min(tolerance * c.multiplier, SCALED_RELATIVE_TOLERANCE * Math.abs(scaled)) : tolerance
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
 * currency in model text (markdown ** and backticks, a hyphen, "m^2"/"m**2" and decimal commas are
 * tolerated) and says whether the given Result contains that value.
 *
 * NOT flagged at all (no figure, no warning):
 * - units it does not list ("1.2 MWh", "0.5 kW", "3 km", "300 kg", "5 pct", "450 dollars",
 *   "2 kelvins"), and raw wire tokens ("12.3 kWh_per_m2", "weighted_m2_h", "GBP_pence");
 * - numbers written after their unit ("Additional shade (m²·h): 99.9"), or glued to a preceding
 *   ".", "," or "_" (".5", "energy,2.5 kWh", "__2__ °C");
 * - temperatures with a space before a bare letter or a bracketed unit ("2 C", "3 C°", "3 (°C)"),
 *   or wrapped in HTML ("<b>2</b> °C") — the backstop below catches only some of these;
 * - money with a spelled scale but no £ or unit ("saves 3 million a year" is a context count);
 * - spelled-out or qualitative claims ("two degrees", "noticeably cooler");
 * - direction words: "reduces by 2.5 kWh" is compared as +2.5. Written signs ("-", "−", "–")
 *   are compared strictly, so only a written sign can contradict a stored sign;
 * - the lower bound of a range ("10-12 m²·h" checks only 12).
 * Falsely marked `appears-in-result` (the narrative is still labelled interpretation): "£450 000"
 * and "£450 grand" (read as £450), "(£450)" accounting negatives (read as +£450), the first half of
 * "£450-900", "MM"/"mil" scales, and "GBP pence" (read as pounds).
 * Known false alarms (fail safe): matching is case-insensitive, so "Table 2c" or "Fig 3f" reads as a
 * temperature; an unspaced list "12,13 m²·h" reads as 12.13; and the temperature backstop fires on
 * "45° from north"-style text that mentions an angle next to "F".
 * Scaled figures may round by their written precision but never by more than 5% of their value.
 * `narrativeView` adds a temperature backstop for unparsed forms. Bare counts and identifiers
 * ("3 trees", "revision 2", "C5") are left alone. Pass `null` evidence when no validated Result
 * is attached.
 */
export function narrativeFigures(text: string, evidence: NarrativeEvidence | null): NarrativeFigure[] {
  const figures: NarrativeFigure[] = []
  for (const match of normalise(text).matchAll(FIGURE)) {
    const [whole, currency, numberText, scale, unit] = match
    const gluedScale = Boolean(scale) && whole.includes(numberText + scale)
    const c = classify((currency ?? '').replace(/\s+/g, ''), scale ?? '', unit ?? '', gluedScale)
    if (!c) continue
    const parsed = parseNumber(numberText)
    const value = c.negative ? -parsed : parsed
    if (!Number.isFinite(value)) continue
    figures.push({
      text: whole.trim().replace(/\s+/g, ' '),
      index: match.index ?? 0,
      kind: c.kind,
      status: statusOf(c, value, writtenTolerance(numberText), evidence),
      contextOnly: CONTEXT_ONLY.has(c.kind),
    })
  }
  return figures
}

/** Model prose packaged for display as interpretation, with its figures checked against the Result. */
export function narrativeView(text: string, evidence: NarrativeEvidence | null): NarrativeView {
  const figures = narrativeFigures(text, evidence)
  const temperatureMentioned = TEMPERATURE_NEAR_NUMBER.test(text)
  return {
    label: MODEL_INTERPRETATION_LABEL, text, figures, temperatureMentioned,
    needsWarning: temperatureMentioned || figures.some(f => !f.contextOnly && f.status !== 'appears-in-result'),
  }
}
