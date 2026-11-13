import type { Layout, Result, Scenario, SiteBundle, TreeProfile, TreeState, Vec3 } from '../api/types'
import { CURRENTNESS_LABEL, formatPence, samePosition, type Currentness } from './evaluation'

/**
 * View model for the B08 selected-tree inspector. Every value comes from a contract field:
 * the layout placement, the site's candidate catalogue, the loaded tree profile, the accepted
 * scenario and, when one exists, a stored Result that evaluated exactly this layout revision.
 *
 * What the backend cannot supply is said plainly rather than estimated:
 *  - No operation measures one tree's shade (no remove-one or per-placement metric exists), so
 *    that row is always "Not calculated" and never derived from a layout total.
 *  - Constraint records carry a layout_id but no placement id, so they are labelled layout-level.
 *  - No shadow footprint figures are produced here.
 */

type Candidate = SiteBundle['candidate_catalogue'][number]
type Placement = Layout['placements'][number]
type EvaluatedLayout = Result['layouts'][number]
type ConstraintRecord = Result['constraints'][number]
type ConstraintUnit = NonNullable<ConstraintRecord['unit']>

export const NOT_RECORDED = 'Not recorded'
export const NOT_LOADED = 'Not loaded'
export const MARGINAL_LABEL = 'Shade from this tree alone'
export const MARGINAL_NOT_CALCULATED = 'Not calculated — no per-tree operation exists'
export const MARGINAL_EXPLANATION =
  'Runs report shade for the whole layout. No remove-one or per-placement figure is computed, so none is shown.'
export const CONSTRAINTS_LAYOUT_LEVEL =
  'Layout-level: the backend records constraints for the whole layout, not for this tree.'

export type Tone = 'plain' | 'ok' | 'warn' | 'bad' | 'muted'

export interface InspectorRow {
  readonly label: string
  readonly value: string
  readonly tone: Tone
  readonly mono: boolean
  /** Short uppercase tag shown before the value, e.g. ASSUMPTION. */
  readonly tag: string | null
}

export interface StateRow {
  readonly key: string
  readonly heading: string
  readonly crown: string
  readonly trunk: string
  readonly light: string
  /** Evaluation cases (id and role) that use this state, from the scenario. */
  readonly usedBy: string
  /** True when the scenario's primary case uses this state. */
  readonly primary: boolean
}

export interface ConstraintRow {
  readonly rule: string
  readonly status: ConstraintRecord['status']
  readonly statusLabel: string
  readonly detail: string | null
}

/** A stored Result that evaluated exactly the inspected layout revision, with its currentness. */
export interface TreeEvidence {
  readonly result: Result
  readonly evaluated: EvaluatedLayout
  readonly currentness: Currentness
}

export interface TreeInspectorInput {
  readonly placementId: string | null
  /** The layout holding the placement: the scenario's proposed layout, or a layout from a stored Result. */
  readonly layout: Layout | null
  readonly catalogue: readonly Candidate[]
  readonly profiles: readonly TreeProfile[]
  readonly scenario: Pick<Scenario, 'scenario_id' | 'revision' | 'scope' | 'input'> | null
  readonly evidence: TreeEvidence | null
  /** Unaccepted position of this placement; pass null unless the layout is the editable proposed layout. */
  readonly draftPosition: Vec3 | null
}

export type InspectorView =
  | { readonly kind: 'empty'; readonly title: string; readonly detail: string }
  | { readonly kind: 'missing'; readonly title: string; readonly detail: string }
  | {
      readonly kind: 'tree'
      readonly title: string
      readonly subtitle: string
      readonly badge: { readonly label: string; readonly tone: Tone }
      readonly identity: readonly InspectorRow[]
      readonly position: readonly InspectorRow[]
      readonly marginal: InspectorRow
      readonly profile: readonly InspectorRow[]
      readonly states: readonly StateRow[]
      readonly evaluation: readonly InspectorRow[]
      readonly evaluationNote: string
      readonly constraints: readonly ConstraintRow[]
      readonly constraintNote: string
    }

const row = (label: string, value: string, tone: Tone = 'plain', mono = false, tag: string | null = null): InspectorRow => ({ label, value, tone, mono, tag })

/** Up to millimetres, without float noise or a negative zero. */
export const metres = (x: number) => String(Number(x.toFixed(3)) + 0)

const short = (value: string, n = 10) => (value.length > n + 1 ? `${value.slice(0, n)}…` : value)

const orNotRecorded = (text: string | null | undefined) => (text && text.trim() !== '' ? text : NOT_RECORDED)

const countOf = (items: readonly string[], noun: string) =>
  items.length === 0 ? NOT_RECORDED : `${items.length} ${noun}${items.length === 1 ? '' : 's'}`

export const formatEnu = (p: readonly number[]) => `E ${metres(p[0])} m · N ${metres(p[1])} m · U ${metres(p[2])} m`

const PLANTABILITY: Record<Candidate['plantability_status'], { label: string; tone: Tone }> = {
  documented_model_region: { label: 'Inside a documented model region', tone: 'plain' },
  provisional: { label: 'Provisional position', tone: 'warn' },
  excluded: { label: 'Excluded position', tone: 'bad' },
}

const FEASIBILITY: Record<EvaluatedLayout['feasibility'], { label: string; tone: Tone }> = {
  feasible: { label: 'Feasible (whole layout)', tone: 'ok' },
  infeasible: { label: 'Infeasible (whole layout)', tone: 'bad' },
  not_evaluated: { label: 'Not evaluated', tone: 'muted' },
}

const STATUS_LABEL: Record<ConstraintRecord['status'], string> = { pass: 'Pass', fail: 'Fail', unknown: 'Unknown' }

const UNIT: Record<Exclude<ConstraintUnit, 'GBP_pence'>, string> = {
  m: 'm', m2: 'm²', h: 'h', m2_h: 'm²·h', weighted_m2_h: 'weighted m²·h', kWh: 'kWh', kWh_per_m2: 'kWh/m²',
}

const quantity = (value: number, unit: ConstraintRecord['unit']) =>
  unit === 'GBP_pence' ? formatPence(value) : unit === null ? metres(value) : `${metres(value)} ${UNIT[unit]}`

export function describeConstraint(record: ConstraintRecord): ConstraintRow {
  const parts: string[] = []
  if (record.observed_value !== null) parts.push(`observed ${quantity(record.observed_value, record.unit)}`)
  if (record.limit !== null) parts.push(`limit ${quantity(record.limit, record.unit)}`)
  if (record.case_id !== null) parts.push(`case ${record.case_id}`)
  return { rule: record.rule, status: record.status, statusLabel: STATUS_LABEL[record.status], detail: parts.length ? parts.join(' · ') : null }
}

export function describeAttenuation(attenuation: TreeState['attenuation']): string {
  if (attenuation.mode === 'opaque') return 'opaque crown (assumed)'
  return attenuation.transmission !== null && attenuation.transmission !== undefined
    ? `fixed transmission ${attenuation.transmission} (assumed)`
    : 'fixed transmission, value not recorded'
}

const sameLayout = (a: Pick<Layout, 'layout_id' | 'revision'>, b: Pick<Layout, 'layout_id' | 'revision'>) =>
  a.layout_id === b.layout_id && a.revision === b.revision

/**
 * The stored Result that evaluated exactly this layout revision. The backend-selected run wins when it
 * contains the layout, because arrival order can put a late older job first; otherwise the newest
 * matching run (runs are newest first). Returns null when no stored result evaluates this revision.
 */
export function layoutEvidence(
  runs: ReadonlyArray<{ readonly result: Result | null }>,
  layout: Pick<Layout, 'layout_id' | 'revision'> | null,
  currentness: (result: Result) => Currentness,
  selectedRunId: string | null = null,
): TreeEvidence | null {
  if (!layout) return null
  const evaluatedIn = (result: Result | null): EvaluatedLayout | null =>
    result?.layouts.find(e => sameLayout(e.layout, layout)) ?? null
  const ordered = selectedRunId
    ? [...runs.filter(r => r.result?.run_id === selectedRunId), ...runs.filter(r => r.result?.run_id !== selectedRunId)]
    : runs
  for (const run of ordered) {
    const evaluated = evaluatedIn(run.result)
    if (run.result && evaluated) return { result: run.result, evaluated, currentness: currentness(run.result) }
  }
  return null
}

function candidateFor(catalogue: readonly Candidate[], placement: Placement): Candidate | null {
  if (placement.candidate_id !== null) return catalogue.find(c => c.candidate_id === placement.candidate_id) ?? null
  return catalogue.find(c => c.location_id === placement.location_id && c.profile_id === placement.profile_id) ?? null
}

function stateRows(profile: TreeProfile, scenario: TreeInspectorInput['scenario']): StateRow[] {
  const cases = scenario?.input.evaluation_cases ?? []
  const primaryState = cases.find(c => c.case_id === scenario?.input.objective.primary_case_id)?.profile_state ?? null
  return Object.entries(profile.states)
    .sort(([ka, a], [kb, b]) => a.horizon_years - b.horizon_years || ka.localeCompare(kb))
    .map(([key, s]) => {
      const users = cases.filter(c => c.profile_state === key).map(c => `${c.case_id} (${c.role})`)
      return {
        key,
        heading: `${key} · year ${metres(s.horizon_years)}`,
        crown: `Crown radii ${s.crown_radii_m.map(metres).join(' / ')} m · centre ${metres(s.crown_center_height_m)} m`,
        trunk: `Trunk ${metres(s.trunk_height_m)} m high · r ${metres(s.trunk_radius_m)} m · leaves ${orNotRecorded(s.leaf_state)}`,
        light: describeAttenuation(s.attenuation),
        usedBy: users.length ? users.join(', ') : scenario ? 'No evaluation case uses this state' : NOT_LOADED,
        primary: primaryState === key,
      }
    })
}

export function inspectTree(input: TreeInspectorInput): InspectorView {
  const { placementId, layout, catalogue, profiles, scenario, evidence, draftPosition } = input
  if (!placementId || !layout) {
    return { kind: 'empty', title: 'No tree selected', detail: 'Select a proposed tree to see its position, profile and stored evaluation.' }
  }
  const placement = layout.placements.find(p => p.placement_id === placementId)
  if (!placement) {
    return {
      kind: 'missing',
      title: `${placementId} is not in this layout`,
      detail: `Layout ${layout.layout_id} revision ${layout.revision} has no placement with that id. Select the tree again.`,
    }
  }

  const candidate = candidateFor(catalogue, placement)
  const proposedRef = scenario?.input.proposed_layout_ref ?? null
  const isScenarioLayout = proposedRef !== null && sameLayout(proposedRef, layout)

  const plantability = candidate ? PLANTABILITY[candidate.plantability_status] : null
  const identity: InspectorRow[] = [
    row('Placement', placement.placement_id, 'plain', true),
    row('Location', placement.location_id, 'plain', true),
    row('Catalogue candidate', placement.candidate_id ?? NOT_RECORDED, placement.candidate_id ? 'plain' : 'muted', true),
    row('Plantability', plantability ? plantability.label : NOT_RECORDED, plantability ? plantability.tone : 'muted'),
    row('Position sources', candidate ? countOf(candidate.source_ids, 'source') : NOT_RECORDED, candidate && candidate.source_ids.length ? 'plain' : 'muted'),
    row('Pinned', placement.pinned ? 'Pinned by the scenario' : 'Not pinned'),
    row('Layout', `${layout.layout_id} · rev ${layout.revision} · ${layout.kind}`, 'plain', true),
    scenario
      ? row(
          'Scenario',
          `${scenario.scenario_id} · rev ${scenario.revision} (${scenario.scope})${isScenarioLayout ? '' : ' · not its proposed layout'}`,
          isScenarioLayout ? 'plain' : 'warn',
          true,
        )
      : row('Scenario', NOT_LOADED, 'muted'),
  ]

  const position: InspectorRow[] = [row('Position (ENU)', formatEnu(placement.position_enu_m), 'plain', true)]
  if (draftPosition && !samePosition(draftPosition, placement.position_enu_m as Vec3)) {
    position.push(row('Draft position', `${formatEnu(draftPosition)} · not accepted`, 'warn', true, 'DRAFT'))
  }

  const profile = profiles.find(p => p.profile_id === placement.profile_id) ?? null
  const profileRows: InspectorRow[] = profile
    ? [
        row('Profile', `${profile.profile_id} · ${orNotRecorded(profile.species_size_label)}`),
        row('Upfront cost', `${formatPence(profile.cost_pence)} · ${orNotRecorded(profile.cost_scope)}`, 'warn', false, 'ASSUMPTION'),
        row('Price date', orNotRecorded(profile.price_date), profile.price_date ? 'plain' : 'muted', true),
        row('Profile library', `rev ${profile.library_revision}`, 'plain', true),
        row('Profile sources', countOf(profile.source_ids, 'source'), profile.source_ids.length ? 'plain' : 'muted'),
        row('Profile assumptions', countOf(profile.assumption_ids, 'assumption'), profile.assumption_ids.length ? 'plain' : 'muted'),
      ]
    : [row('Profile', `${placement.profile_id} · details ${NOT_LOADED.toLowerCase()}`, 'muted', true)]

  let evaluation: InspectorRow[] = []
  let evaluationNote = 'No stored result evaluates this layout revision yet. Feasibility and constraints appear after an evaluation of this exact layout.'
  let constraints: ConstraintRow[] = []
  let constraintNote = CONSTRAINTS_LAYOUT_LEVEL
  if (evidence) {
    const { result, evaluated, currentness } = evidence
    const feasibility = FEASIBILITY[evaluated.feasibility]
    evaluation = [
      row('Result', `${CURRENTNESS_LABEL[currentness].label} · run ${short(result.run_id)}`, currentness === 'current' ? 'ok' : 'warn', true),
      row('Operation', result.operation, 'plain', true),
      row('Layout feasibility', feasibility.label, feasibility.tone),
      ...(evaluated.reasons.length ? [row('Reasons', evaluated.reasons.join('; '), feasibility.tone === 'ok' ? 'plain' : 'warn')] : []),
      row('Layout cost', `${formatPence(evaluated.cost_pence)} · whole layout`, 'plain', true),
      row('Trees in layout', String(evaluated.tree_count), 'plain', true),
    ]
    evaluationNote = CURRENTNESS_LABEL[currentness].detail
    constraints = result.constraints.filter(c => c.layout_id === evaluated.layout.layout_id).map(describeConstraint)
    if (constraints.length === 0) constraintNote = 'The stored result records no constraints for this layout.'
  }

  const badge: { label: string; tone: Tone } = isScenarioLayout && scenario
    ? { label: `REV ${scenario.revision}`, tone: 'ok' }
    : { label: `LAYOUT REV ${layout.revision}`, tone: 'muted' }

  return {
    kind: 'tree',
    title: placement.placement_id,
    subtitle: `${placement.candidate_id ? `candidate ${placement.candidate_id}` : 'no catalogue candidate'} · ${placement.pinned ? 'pinned' : 'not pinned'}`,
    badge,
    identity,
    position,
    marginal: row(MARGINAL_LABEL, MARGINAL_NOT_CALCULATED, 'muted', false, 'NOT COMPUTED'),
    profile: profileRows,
    states: profile ? stateRows(profile, scenario) : [],
    evaluation,
    evaluationNote,
    constraints,
    constraintNote,
  }
}
