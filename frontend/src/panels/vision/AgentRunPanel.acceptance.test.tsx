// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Job, Metric, Result, Scenario } from '../../api/types'
import { linkageProblems, MODEL_INTERPRETATION_LABEL } from '../../planning/agentEvidence'
import { AGENT_TRANSPORT_UNAVAILABLE_REASON, type AgentAvailability, type AgentRunSnapshot, type AgentRunTransport, type AgentToolStep } from '../../planning/agentRun'
import { useAgentRun } from '../../planning/useAgentRun'
import type { RunRecord, Workspace } from '../../planning/useWorkspace'
import { AgentRunPanel } from './AgentRunPanel'

// Independent acceptance tests for the agent-run panel, written from the shared interface and behaviour
// rules only. LABELLED SYNTHETIC TEST DOUBLES AND INPUTS: `SyntheticTransport` is a controllable fake,
// `fakeWorkspace` a hand-made Workspace, and the Job/Result records are contract-shaped synthetic inputs
// (as in agentEvidence.test.ts), not runtime results. No agent-run API exists in this build (#73).

type StartRequest = Parameters<AgentRunTransport['start']>[0]
interface Pending<T> { readonly promise: Promise<T>; settled: boolean; resolve(value: T): void; reject(error: unknown): void }
function pending<T>(): Pending<T> {
  let res!: (value: T) => void
  let rej!: (error: unknown) => void
  const promise = new Promise<T>((resolve, reject) => { res = resolve; rej = reject })
  const p: Pending<T> = {
    promise, settled: false,
    resolve: value => { p.settled = true; res(value) },
    reject: error => { p.settled = true; rej(error) },
  }
  return p
}
class SyntheticTransport implements AgentRunTransport {
  availability: AgentAvailability = { kind: 'available', model: 'synthetic-test-double' }
  readonly starts: Array<{ readonly req: StartRequest; readonly reply: Pending<AgentRunSnapshot> }> = []
  readonly gets: Array<{ readonly id: string; readonly reply: Pending<AgentRunSnapshot> }> = []
  readonly cancels: Array<{ readonly id: string; readonly reply: Pending<AgentRunSnapshot> }> = []
  status = () => Promise.resolve(this.availability)
  start = (req: StartRequest) => { const reply = pending<AgentRunSnapshot>(); this.starts.push({ req, reply }); return reply.promise }
  get = (id: string) => { const reply = pending<AgentRunSnapshot>(); this.gets.push({ id, reply }); return reply.promise }
  cancel = (id: string) => { const reply = pending<AgentRunSnapshot>(); this.cancels.push({ id, reply }); return reply.promise }
}
const snap = (over: Partial<AgentRunSnapshot> = {}): AgentRunSnapshot => ({
  agentRunId: 'ar-1', seq: 1, phase: 'running', steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, ...over,
})
const step = (over: Partial<AgentToolStep> = {}): AgentToolStep => ({
  seq: 1, tool: 'evaluate_layout', status: 'completed', jobId: 'job-1', runId: 'run-1', error: null, ...over,
})

// Synthetic contract-shaped Job/Result (see agentEvidence.test.ts for the field rationale).
const FP = 'a'.repeat(64)
const ref = { scenario_id: 's1', revision: 3, scope: 'accepted' as const }
const metric: Metric = {
  case_id: 'summer', horizon_years: 10, layout_id: 'L1', metric_id: 'additional_shade', metric_instance_id: 'm1',
  quantity_kind: 'geometric', scenario_ref: ref, target_id: null, unit: 'm2_h', value: 12.34, weighting: 'unweighted',
} as Metric
const delivery = (over: Record<string, unknown> = {}) => ({
  delivered_at_utc: '2026-11-13T12:00:00Z', execution_mode: 'live', input_fingerprint: FP, job_id: 'job-1', run_id: 'run-1',
  scenario_id: 's1', scenario_revision: 3, scope: 'accepted', selection_seq: 1, source_job_id: 'job-1', view_slot: 'evaluation', ...over,
})
const job = (over: Record<string, unknown> = {}): Job => ({
  job_id: 'job-1', request_id: 'req-job-1', status: 'completed', run_id: 'run-1', operation: 'evaluate_layout', scenario_id: 's1', scenario_revision: 3,
  scope: 'accepted', input_fingerprint: FP, view_slot: 'evaluation', selection_seq: 1, progress: null, cancel_requested: false,
  superseded_by_revision: null, error: null, delivery: delivery(), ...over,
} as unknown as Job)
const result = (over: Record<string, unknown> = {}): Result => ({
  run_id: 'run-1', source_job_id: 'job-1', input_fingerprint: FP, input_snapshot_ref: ref, scenario_id: 's1', scenario_revision: 3, scope: 'accepted',
  operation: 'evaluate_layout', analytical_outcome: 'comparison_completed', metrics: [metric], missing_metrics: [], constraints: [], assumptions: [],
  layouts: [{ cost_pence: 45000, selected: false, role: 'alternative', feasibility: 'not_evaluated', reasons: ['Constraints not evaluated'], scenario_ref: ref, layout: { layout_id: 'L1' } }],
  limitations: ['Synthetic flat site; one-hour sample.'], provenance: { execution_mode: 'live' }, ...over,
} as unknown as Result)
const record = (j: Job, r: Result): RunRecord => ({ job: j, result: r, inputScenario: null })
/** The backend figures the chain must show, and that must never appear from anywhere else. */
const FIGURES = ['12.34 m²·h', '£450.00']
const FIGURE_FRAGMENTS = ['12.34', '450.00', '£450', 'm²·h']

const scenarioAt = (revision: number, scenarioId = 's1'): Scenario => ({
  scenario_id: scenarioId, revision, scope: 'accepted', base_scenario_ref: null,
  input: {
    site_id: 'site', scene_revision: 1, semantic_revision: 1, profile_library_revision: 1, candidate_catalogue_revision: 1,
    proposed_layout_ref: { layout_id: 'L', revision: 1 },
    constraints: { budget_pence: 10_000, budget_basis: 'upfront', max_tree_count: null, excluded_region_ids: [], allowed_profile_ids: [], spacing_rules: [], winter_limits: [], pinned_placements: [], survey_requirements: [] },
    objective: { kind: 'maximise_shade_under_budget', primary_case_id: 'c', quantity_kind: 'geometric' },
    evaluation_cases: [{ case_id: 'c', profile_state: 'mature', role: 'benefit' }],
    search: { deadline_utc: '2099-01-01T00:00:00Z' },
  },
} as unknown as Scenario)
const noop = () => {}
const resolved = async () => {}
function fakeWorkspace(over: Partial<Workspace> = {}): Workspace {
  const base: Workspace = {
    connection: { status: 'connected', health: { status: 'ok', version: 't', schema_version: '0.1.0', worker_mode: 'background', available_operations: ['evaluate_layout'] } },
    session: null, declaration: null, site: null, profile: null, scenario: scenarioAt(3), layout: null, placementId: null,
    committedPosition: null, draftPosition: null, positionDirty: false, acceptedRequirements: null, draftRequirements: null,
    requirementsDirty: false, requirementErrors: [], draftChanges: [], draftDirty: false, activeJob: null, jobStatusLost: false,
    runs: [], currentRunId: null, currentRunIds: { evaluation: null, search: null, comparison: null }, busy: null, notice: null,
    error: null, canEvaluate: true, editPending: false, setEditPending: noop, review: null, currentness: () => 'current',
    setDraftPosition: noop, setDraftRequirements: noop, revertDraft: noop, evaluate: resolved, submit: resolved, cancel: resolved,
    recheckJob: resolved, loadProposal: resolved, acceptProposal: resolved, dismissProposal: noop, reload: noop,
  }
  return { ...base, ...over }
}

const QUESTION = 'Evaluate the proposed planting layout'
const flush = () => act(async () => { await vi.advanceTimersByTimeAsync(0) })
const advance = (ms: number) => act(async () => { await vi.advanceTimersByTimeAsync(ms) })
async function settle<T>(p: Pending<T>, value: T | Error) {
  await act(async () => { if (value instanceof Error) p.reject(value); else p.resolve(value) })
  await flush()
}
async function nextGet(t: SyntheticTransport) {
  const open = t.gets.find(g => !g.reply.settled)
  if (open) return open
  const n = t.gets.length
  for (let ms = 0; ms < 120_000 && t.gets.length === n; ms += 250) await advance(250)
  expect(t.gets.length).toBeGreaterThan(n)
  return t.gets[n]
}

/** The real hook driven by the synthetic transport, handed to the panel as its controller. */
function WithTransport({ ws, transport }: { ws: Workspace; transport: AgentRunTransport }) {
  return <AgentRunPanel ws={ws} controller={useAgentRun(ws, transport)} />
}
/**
 * The only place the panel's props appear (the shared interface does not fix them): with no transport
 * the panel runs its own default hook (unavailable transport); otherwise the real hook is driven by
 * the synthetic transport.
 */
function mount(ws: Workspace, transport?: AgentRunTransport) {
  const el = (w: Workspace) => (transport ? <WithTransport ws={w} transport={transport} /> : <AgentRunPanel ws={w} />)
  const view = render(el(ws))
  return { ...view, update: (next: Workspace) => view.rerender(el(next)) }
}
const panelText = (root: HTMLElement) => root.textContent ?? ''
const isDisabled = (el: HTMLElement) => (el as HTMLInputElement | HTMLButtonElement | HTMLTextAreaElement).disabled === true
const startButton = () => screen.getByRole('button', { name: /start/i })
async function ask(question = QUESTION) {
  fireEvent.change(screen.getByRole('textbox'), { target: { value: question } })
  fireEvent.click(startButton())
  await flush()
}
async function completedRun(ws: Workspace, final: Partial<AgentRunSnapshot>) {
  const t = new SyntheticTransport()
  const view = mount(ws, t)
  await flush()
  await ask()
  expect(t.starts).toHaveLength(1)
  await settle(t.starts[0].reply, snap({ seq: 1, phase: 'completed', outcome: 'completed_with_evidence', ...final }))
  return { t, view }
}
/** Text of `root` outside `exclude`, element by element (text nodes only). */
function textOutside(root: HTMLElement, exclude: Element): string {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT)
  let out = ''
  for (let n = walker.nextNode(); n; n = walker.nextNode()) if (!exclude.contains(n)) out += `${n.textContent ?? ''} `
  return out
}
function smallestContaining(root: HTMLElement, text: string): HTMLElement | null {
  const all = [root, ...Array.from(root.querySelectorAll<HTMLElement>('*'))].filter(e => (e.textContent ?? '').includes(text))
  return all.sort((a, b) => (a.textContent ?? '').length - (b.textContent ?? '').length)[0] ?? null
}
const FORBIDDEN = [/\boptimal\b/i, /\boptimi[sz]/i, /\bprove[ns]?\b|\bproving\b/i, /\bverified\b/i, /\breal site\b/i, /\bmeasured shade\b/i]
function forbiddenWords(root: HTMLElement): string[] {
  const attrs = Array.from(root.querySelectorAll('*')).flatMap(e => ['aria-label', 'title', 'placeholder', 'alt', 'aria-description'].map(a => e.getAttribute(a) ?? ''))
  const all = [panelText(root), ...attrs].join(' \n ')
  return FORBIDDEN.filter(re => re.test(all)).map(String)
}
function liveRegion(root: HTMLElement): HTMLElement {
  const el = root.querySelector<HTMLElement>('[aria-live="polite"], [role="status"]')
  expect(el).not.toBeNull()
  return el!
}

beforeEach(() => { vi.useFakeTimers() })
afterEach(() => { cleanup(); vi.useRealTimers() }) // vitest globals are off, so RTL's auto-cleanup does not run

describe('AgentRunPanel acceptance: agent unavailable fallback', () => {
  it('disables the request box and Start, shows the reason and says manual planning is unaffected', async () => {
    const { container } = mount(fakeWorkspace())
    await flush()
    expect(isDisabled(screen.getByRole('textbox'))).toBe(true)
    expect(isDisabled(startButton())).toBe(true)
    expect(panelText(container)).toContain(AGENT_TRANSPORT_UNAVAILABLE_REASON)
    // Same sentence must say manual planning is unaffected; the panel may name the manual tools in between.
    expect(panelText(container)).toMatch(/manual planning\b[^.]*\bis unaffected/i)
    expect(panelText(container)).toMatch(/not connected|unavailable/i)
    expect(panelText(container)).not.toContain(MODEL_INTERPRETATION_LABEL) // no fabricated answer
  })
})

describe('AgentRunPanel acceptance: real Job -> Result evidence binding', () => {
  it('with a matching record in ws.runs it shows the backend chain values', async () => {
    const ws = fakeWorkspace({ runs: [record(job(), result())], currentRunIds: { evaluation: 'run-1', search: null, comparison: null }, currentRunId: 'run-1' })
    const { view } = await completedRun(ws, { steps: [step()], evidenceIds: ['run-1'] })
    const text = panelText(view.container)
    for (const figure of FIGURES) expect(text).toContain(figure)
    expect(text).toContain('job-1')
    expect(text).toContain('run-1')
  })

  it('with no record it shows only the ids and "Result not loaded in this workspace"', async () => {
    const { view } = await completedRun(fakeWorkspace({ runs: [] }), { steps: [step()], evidenceIds: ['run-1'] })
    const text = panelText(view.container)
    expect(text).toContain('job-1')
    expect(text).toContain('run-1')
    expect(text).toContain('Result not loaded in this workspace')
    for (const fragment of FIGURE_FRAGMENTS) expect(text).not.toContain(fragment)
  })

  it('with a mismatched record (different input fingerprint) it shows the problems and no figures', async () => {
    const bad = record(job(), result({ input_fingerprint: 'b'.repeat(64) }))
    const problems = linkageProblems(bad.job, bad.result!)
    expect(problems.length).toBeGreaterThan(0)
    const { view } = await completedRun(fakeWorkspace({ runs: [bad] }), { steps: [step()], evidenceIds: ['run-1'] })
    const text = panelText(view.container)
    for (const p of problems) expect(text).toContain(p)
    for (const fragment of FIGURE_FRAGMENTS) expect(text).not.toContain(fragment)
  })

  it('with a mismatched record (other source job on a live delivery) it shows the problems and no figures', async () => {
    const bad = record(job({ delivery: delivery({ source_job_id: 'job-0' }) }), result({ source_job_id: 'job-0' }))
    const problems = linkageProblems(bad.job, bad.result!)
    expect(problems.length).toBeGreaterThan(0)
    const { view } = await completedRun(fakeWorkspace({ runs: [bad] }), { steps: [step()], evidenceIds: ['run-1'] })
    const text = panelText(view.container)
    for (const p of problems) expect(text).toContain(p)
    for (const fragment of FIGURE_FRAGMENTS) expect(text).not.toContain(fragment)
  })
})

describe('AgentRunPanel acceptance: invalid or missing tool evidence', () => {
  it('a step with neither jobId nor runId shows no figures, even when ws.runs holds a valid record', async () => {
    const ws = fakeWorkspace({ runs: [record(job(), result())], currentRunIds: { evaluation: 'run-1', search: null, comparison: null }, currentRunId: 'run-1' })
    const { view } = await completedRun(ws, { steps: [step({ jobId: null, runId: null })], evidenceIds: [] })
    const text = panelText(view.container)
    expect(text).toContain('evaluate_layout')
    for (const fragment of FIGURE_FRAGMENTS) expect(text).not.toContain(fragment)
  })
})

describe('AgentRunPanel acceptance: no false numerical claims', () => {
  it('model narrative is shown under the interpretation label, flagged, and its numbers appear nowhere else', async () => {
    const NARRATIVE = 'This cools the street by 3 °C and saves £1.2m a year.'
    const ws = fakeWorkspace({ runs: [record(job(), result())], currentRunIds: { evaluation: 'run-1', search: null, comparison: null }, currentRunId: 'run-1' })
    const { view } = await completedRun(ws, { steps: [step()], evidenceIds: ['run-1'], narrative: NARRATIVE })
    const root = view.container
    const narrativeEl = smallestContaining(root, NARRATIVE)
    expect(narrativeEl).not.toBeNull()
    let block: HTMLElement | null = narrativeEl
    while (block && !/interpretation/i.test(block.textContent ?? '')) block = block.parentElement
    expect(block).not.toBeNull()
    expect(block!.contains(startButton())).toBe(false) // the interpretation block is its own region, not the whole panel
    expect(block!.textContent).toMatch(/model interpretation/i)
    // Flagged: the block says more than the label and the text (a figure warning or a check prompt).
    const extra = (block!.textContent ?? '').replace(NARRATIVE, '').replace(MODEL_INTERPRETATION_LABEL, '')
    expect(extra).toMatch(/°C|temperature|unsupported|not traceable|unverified|not computed|check|cannot|warning|flag/i)
    const outside = textOutside(root, block!)
    expect(outside).not.toMatch(/°\s*C/)
    expect(outside).not.toMatch(/1\.2\s*m\b|£\s*1\.2|\b1\.2\b/)
    expect(outside).not.toMatch(/\bcools\b|\bsaves\b/i)
    // The backend figures are still shown, from the chain.
    for (const figure of FIGURES) expect(outside).toContain(figure)
  })
})

describe('AgentRunPanel acceptance: accessibility basics', () => {
  it('named request field, polite live status, and named Start/Stop/Re-check/Clear buttons', async () => {
    const t = new SyntheticTransport()
    const { container } = mount(fakeWorkspace(), t)
    await flush()
    expect(isDisabled(screen.getByRole('textbox', { name: /\S/ }))).toBe(false)
    expect(startButton().tagName).toBe('BUTTON')
    await ask()
    await settle(t.starts[0].reply, snap({ seq: 1, phase: 'running' }))
    expect(liveRegion(container).textContent).toMatch(/running/i)
    const stop = screen.getByRole('button', { name: /stop/i })
    fireEvent.click(stop)
    await flush()
    expect(t.cancels).toHaveLength(1)
    await settle(t.cancels[0].reply, new Error('no reply'))
    expect(liveRegion(container).textContent).toMatch(/unknown/i)
    expect(isDisabled(screen.getByRole('button', { name: /re-?check/i }))).toBe(false)
    fireEvent.click(screen.getByRole('button', { name: /clear/i }))
    await flush()
    expect(screen.queryByRole('button', { name: /re-?check/i })).toBeNull()
  })
})

describe('AgentRunPanel acceptance: wording', () => {
  it('the panel in every phase contains none of the forbidden words', async () => {
    const seen: Record<string, string[]> = {}
    const check = (label: string, root: HTMLElement) => { seen[label] = forbiddenWords(root) }

    const unavailable = mount(fakeWorkspace())
    await flush()
    check('unavailable', unavailable.container)
    unavailable.unmount()

    const ws = fakeWorkspace({ runs: [record(job(), result())], currentRunIds: { evaluation: 'run-1', search: null, comparison: null }, currentRunId: 'run-1' })
    const t = new SyntheticTransport()
    const view = mount(ws, t)
    await flush()
    check('idle', view.container)
    await ask()
    check('submitting', view.container)
    await settle(t.starts[0].reply, snap({ seq: 1, phase: 'running', steps: [step({ status: 'running', runId: null })], evidenceIds: [] }))
    check('running', view.container)
    fireEvent.click(screen.getByRole('button', { name: /stop/i }))
    await flush()
    await settle(t.cancels[0].reply, snap({ seq: 2, phase: 'stop_requested' }))
    check('stop_requested', view.container)
    await settle((await nextGet(t)).reply, snap({ seq: 3, phase: 'stopped', outcome: 'stopped' }))
    check('stopped', view.container)
    fireEvent.click(screen.getByRole('button', { name: /clear/i }))
    await flush()

    await ask()
    await settle(t.starts[1].reply, snap({ agentRunId: 'ar-2', seq: 1, phase: 'completed', outcome: 'completed_with_evidence', steps: [step()], evidenceIds: ['run-1'], narrative: 'The layout was evaluated by the backend.' }))
    check('completed', view.container)
    view.update(fakeWorkspace({ ...ws, scenario: scenarioAt(4) }))
    await flush()
    check('completed, head moved', view.container)
    view.update(ws)
    await flush()
    fireEvent.click(screen.getByRole('button', { name: /clear/i }))
    await flush()

    await ask()
    await settle(t.starts[2].reply, snap({ agentRunId: 'ar-3', seq: 1, phase: 'failed', outcome: 'failed', error: 'model protocol error' }))
    check('failed', view.container)
    fireEvent.click(screen.getByRole('button', { name: /clear/i }))
    await flush()

    await ask()
    await settle(t.starts[3].reply, new Error('connection reset'))
    check('status_unknown', view.container)
    // Rule 2: the request may or may not have reached the server, and the UI says so.
    expect(panelText(view.container)).toMatch(/may or may not have reached|may not have reached/i)

    for (const [label, words] of Object.entries(seen)) expect({ label, words }).toEqual({ label, words: [] })
  })
})
