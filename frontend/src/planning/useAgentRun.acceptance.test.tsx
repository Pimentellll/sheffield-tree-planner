// @vitest-environment jsdom
import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Scenario } from '../api/types'
import { isTerminalPhase, type AgentAvailability, type AgentRunSnapshot, type AgentRunTransport } from './agentRun'
import { useAgentRun } from './useAgentRun'
import type { Workspace } from './useWorkspace'

// Independent acceptance tests for useAgentRun, written from the shared interface and behaviour rules
// only. LABELLED SYNTHETIC TEST DOUBLES: `SyntheticTransport` is a controllable fake (every reply is a
// promise the test settles, in any order) and `fakeWorkspace` is a hand-made Workspace. Nothing here is
// agent-run wire data, model output or a runtime result; no agent-run API exists in this build (#73).

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
  holdStatus: Pending<AgentAvailability> | null = null
  readonly starts: Array<{ readonly req: StartRequest; readonly reply: Pending<AgentRunSnapshot> }> = []
  readonly gets: Array<{ readonly id: string; readonly reply: Pending<AgentRunSnapshot> }> = []
  readonly cancels: Array<{ readonly id: string; readonly reply: Pending<AgentRunSnapshot> }> = []
  status = () => (this.holdStatus ? this.holdStatus.promise : Promise.resolve(this.availability))
  start = (req: StartRequest) => { const reply = pending<AgentRunSnapshot>(); this.starts.push({ req, reply }); return reply.promise }
  get = (id: string) => { const reply = pending<AgentRunSnapshot>(); this.gets.push({ id, reply }); return reply.promise }
  cancel = (id: string) => { const reply = pending<AgentRunSnapshot>(); this.cancels.push({ id, reply }); return reply.promise }
}

const snap = (over: Partial<AgentRunSnapshot> = {}): AgentRunSnapshot => ({
  agentRunId: 'ar-1', seq: 1, phase: 'running', steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, ...over,
})

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
async function advanceUntil(done: () => boolean, maxMs = 120_000, stepMs = 250) {
  for (let t = 0; t < maxMs && !done(); t += stepMs) await advance(stepMs)
  expect(done()).toBe(true)
}
async function settle<T>(p: Pending<T>, value: T | Error) {
  await act(async () => { if (value instanceof Error) p.reject(value); else p.resolve(value) })
  await flush()
}
/** The oldest unanswered get(), or the next one the poller issues. */
async function nextGet(t: SyntheticTransport) {
  const open = t.gets.find(g => !g.reply.settled)
  if (open) return open
  const n = t.gets.length
  await advanceUntil(() => t.gets.length > n)
  return t.gets[n]
}

function mount(t: SyntheticTransport | undefined, ws: Workspace = fakeWorkspace()) {
  return renderHook(({ ws: w }: { ws: Workspace }) => (t ? useAgentRun(w, t) : useAgentRun(w)), { initialProps: { ws } })
}
async function runningRun(t: SyntheticTransport, ws?: Workspace) {
  const h = mount(t, ws)
  await flush()
  act(() => h.result.current.submit(QUESTION))
  await flush()
  expect(t.starts).toHaveLength(1)
  await settle(t.starts[0].reply, snap({ seq: 1, phase: 'running' }))
  expect(h.result.current.run?.phase).toBe('running')
  return h
}

beforeEach(() => { vi.useFakeTimers() })
afterEach(() => { cleanup(); vi.useRealTimers(); sessionStorage.clear() }) // vitest globals are off, so RTL's auto-cleanup does not run; an unfinished run is remembered in session storage

describe('useAgentRun acceptance: submit and status lifecycle', () => {
  it('is unavailable by default: no submit, a plain blocked reason, no run', async () => {
    const h = mount(undefined)
    await flush()
    const c = h.result.current
    expect(c.availability?.kind).toBe('unavailable')
    expect(c.canSubmit).toBe(false)
    expect(c.blockedReason).toEqual(expect.any(String))
    act(() => c.submit(QUESTION))
    await flush()
    expect(h.result.current.run).toBeNull()
  })

  it('available -> submitting -> running -> completed, recording the accepted scenario, then polling stops', async () => {
    const t = new SyntheticTransport()
    t.holdStatus = pending<AgentAvailability>()
    const h = mount(t)
    expect(h.result.current.availability).toBeNull()
    expect(h.result.current.canSubmit).toBe(false)
    await settle(t.holdStatus, { kind: 'available', model: 'synthetic-test-double' })
    expect(h.result.current.availability?.kind).toBe('available')
    expect(h.result.current.canSubmit).toBe(true)
    expect(h.result.current.blockedReason).toBeNull()

    act(() => h.result.current.submit(QUESTION))
    await flush()
    expect(h.result.current.run?.phase).toBe('submitting')
    expect(h.result.current.canSubmit).toBe(false)
    expect(t.starts).toHaveLength(1)
    const req = t.starts[0].req
    expect(req.question).toBe(QUESTION)
    expect(req.scenario).toEqual({ scenario_id: 's1', revision: 3, scope: 'accepted' })
    expect(h.result.current.run?.requestId).toBe(req.requestId)
    expect(h.result.current.run?.scenario).toEqual({ scenario_id: 's1', revision: 3, scope: 'accepted' })
    expect(h.result.current.run?.selectedFeatureId).toBe(req.selectedFeatureId)
    expect(h.result.current.run?.agentRunId).toBeNull()

    await settle(t.starts[0].reply, snap({ seq: 1, phase: 'running' }))
    expect(h.result.current.run?.phase).toBe('running')
    expect(h.result.current.run?.agentRunId).toBe('ar-1')

    const g = await nextGet(t)
    expect(g.id).toBe('ar-1')
    await settle(g.reply, snap({ seq: 2, phase: 'completed', outcome: 'completed_with_evidence', narrative: 'synthetic narrative' }))
    expect(h.result.current.run?.phase).toBe('completed')
    expect(h.result.current.run?.outcome).toBe('completed_with_evidence')
    expect(h.result.current.canSubmit).toBe(true)

    const count = t.gets.length
    await advance(120_000)
    expect(t.gets.length).toBe(count)
  })

  it('cannot submit without an accepted scenario or with draft edits', async () => {
    for (const ws of [fakeWorkspace({ scenario: null }), fakeWorkspace({ draftDirty: true, positionDirty: true })]) {
      const t = new SyntheticTransport()
      const h = mount(t, ws)
      await flush()
      expect(h.result.current.canSubmit).toBe(false)
      expect(h.result.current.blockedReason).toEqual(expect.any(String))
      act(() => h.result.current.submit(QUESTION))
      await flush()
      expect(t.starts).toHaveLength(0)
      expect(h.result.current.run).toBeNull()
      h.unmount()
    }
  })

  it('stops polling on unmount', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    await nextGet(t)
    h.unmount()
    const count = t.gets.length
    await advance(120_000)
    expect(t.gets.length).toBe(count)
  })
})

describe('useAgentRun acceptance: duplicate-submit protection and request identity', () => {
  it('double submit creates one start; a later submit gets a new requestId; a retry after a lost reply reuses it', async () => {
    const t = new SyntheticTransport()
    const h = mount(t)
    await flush()
    act(() => { h.result.current.submit(QUESTION); h.result.current.submit(QUESTION) })
    await flush()
    act(() => h.result.current.submit(QUESTION))
    await flush()
    expect(t.starts).toHaveLength(1)
    const first = t.starts[0].req.requestId
    expect(first).toEqual(expect.any(String))

    // Lost reply: the retry must carry the same request identity, question and scenario.
    await settle(t.starts[0].reply, new Error('connection reset'))
    expect(h.result.current.run?.phase).toBe('status_unknown')
    act(() => h.result.current.submit(QUESTION))
    await flush()
    expect(t.starts).toHaveLength(1) // an unknown run is not terminal: no new submit
    act(() => h.result.current.recheck())
    await flush()
    expect(t.starts).toHaveLength(2)
    expect(t.starts[1].req).toEqual(t.starts[0].req)
    expect(h.result.current.run?.requestId).toBe(first)

    await settle(t.starts[1].reply, snap({ seq: 1, phase: 'completed', outcome: 'completed_with_evidence' }))
    expect(h.result.current.run?.phase).toBe('completed')
    act(() => h.result.current.submit('Evaluate it again'))
    await flush()
    expect(t.starts).toHaveLength(3)
    expect(t.starts[2].req.requestId).not.toBe(first)
    expect(h.result.current.run?.requestId).toBe(t.starts[2].req.requestId)
  })
})

describe('useAgentRun acceptance: lost responses', () => {
  it('start() rejecting gives status_unknown with the error text, never failed or running', async () => {
    const t = new SyntheticTransport()
    const h = mount(t)
    await flush()
    act(() => h.result.current.submit(QUESTION))
    await flush()
    await settle(t.starts[0].reply, new Error('connection reset by peer'))
    const run = h.result.current.run
    expect(run?.phase).toBe('status_unknown')
    expect(run?.error).toContain('connection reset by peer')
    expect(h.result.current.canSubmit).toBe(false)
    await advance(60_000)
    expect(h.result.current.run?.phase).toBe('status_unknown')
    expect(t.gets).toHaveLength(0)
  })

  it('get() rejecting gives status_unknown and stops polling; recheck resumes with get()', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    const g = await nextGet(t)
    await settle(g.reply, new Error('poll timed out'))
    expect(h.result.current.run?.phase).toBe('status_unknown')
    expect(h.result.current.run?.error).toContain('poll timed out')
    const count = t.gets.length
    await advance(120_000)
    expect(t.gets.length).toBe(count)
    expect(h.result.current.run?.phase).toBe('status_unknown')

    act(() => h.result.current.recheck())
    await flush()
    expect(t.gets.length).toBe(count + 1)
    expect(t.gets[count].id).toBe('ar-1')
    expect(t.starts).toHaveLength(1) // a known run is re-queried, never re-submitted
    await settle(t.gets[count].reply, snap({ seq: 2, phase: 'running' }))
    expect(h.result.current.run?.phase).toBe('running')
    const resumed = await nextGet(t) // polling resumed
    expect(resumed.id).toBe('ar-1')
  })
})

describe('useAgentRun acceptance: late and out-of-order responses', () => {
  it('an older seq arriving after a newer one changes nothing', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    await settle((await nextGet(t)).reply, snap({ seq: 3, phase: 'running', narrative: 'newer' }))
    await settle((await nextGet(t)).reply, snap({ seq: 2, phase: 'completed', narrative: 'older', outcome: 'completed_with_evidence' }))
    const run = h.result.current.run
    expect(run?.phase).toBe('running')
    expect(run?.narrative).toBe('newer')
    expect(run?.outcome).toBeNull()
    expect(run?.lastSeq).toBe(3)
  })

  it('a reply for a cleared run is dropped', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    await settle((await nextGet(t)).reply, new Error('lost'))
    act(() => h.result.current.recheck())
    await flush()
    const late = t.gets[t.gets.length - 1]
    act(() => h.result.current.clear())
    await flush()
    expect(h.result.current.run).toBeNull()
    await settle(late.reply, snap({ seq: 5, phase: 'completed', outcome: 'completed_with_evidence', narrative: 'late' }))
    expect(h.result.current.run).toBeNull()
  })

  it('a reply for a replaced run is dropped', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    await settle((await nextGet(t)).reply, new Error('lost'))
    act(() => h.result.current.recheck())
    await flush()
    const late = t.gets[t.gets.length - 1]
    act(() => h.result.current.clear())
    await flush()
    act(() => h.result.current.submit('A second question'))
    await flush()
    expect(t.starts).toHaveLength(2)
    await settle(t.starts[1].reply, snap({ agentRunId: 'ar-2', seq: 1, phase: 'running', narrative: 'second' }))
    await settle(late.reply, snap({ agentRunId: 'ar-1', seq: 9, phase: 'completed', narrative: 'first, late', outcome: 'completed_with_evidence' }))
    const run = h.result.current.run
    expect(run?.agentRunId).toBe('ar-2')
    expect(run?.question).toBe('A second question')
    expect(run?.phase).toBe('running')
    expect(run?.narrative).toBe('second')
  })
})

describe('useAgentRun acceptance: cancellation', () => {
  it('stop -> stop_requested (server) -> stopped (server), then polling stops', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    act(() => h.result.current.stop())
    await flush()
    expect(t.cancels).toHaveLength(1)
    expect(t.cancels[0].id).toBe('ar-1')
    expect(h.result.current.run?.phase).not.toBe('stopped') // only the server can say stopped
    await settle(t.cancels[0].reply, snap({ seq: 2, phase: 'stop_requested' }))
    expect(h.result.current.run?.phase).toBe('stop_requested')
    await settle((await nextGet(t)).reply, snap({ seq: 3, phase: 'stopped', outcome: 'stopped' }))
    expect(h.result.current.run?.phase).toBe('stopped')
    const count = t.gets.length
    await advance(120_000)
    expect(t.gets.length).toBe(count)
  })

  it('cancel() rejecting gives status_unknown', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    act(() => h.result.current.stop())
    await flush()
    await settle(t.cancels[0].reply, new Error('cancel not acknowledged'))
    expect(h.result.current.run?.phase).toBe('status_unknown')
    expect(h.result.current.run?.error).toContain('cancel not acknowledged')
  })
})

describe('useAgentRun acceptance: timeout', () => {
  it('a run that never becomes terminal never reports completion', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    let seq = 1
    for (let minute = 0; minute < 30; minute += 1) {
      await advance(60_000)
      for (const g of t.gets.filter(x => !x.reply.settled)) await settle(g.reply, snap({ seq: ++seq, phase: 'running' }))
      const run = h.result.current.run
      expect(run?.phase === 'running' || run?.phase === 'status_unknown').toBe(true)
      expect(run?.outcome).toBeNull()
    }
    expect(isTerminalPhase(h.result.current.run!.phase)).toBe(false)
    expect(h.result.current.canSubmit).toBe(false)
  })
})

describe('useAgentRun acceptance: revision and currentness', () => {
  it('headMoved when the accepted head advances past the run revision, same scenario only; the run is kept', async () => {
    const t = new SyntheticTransport()
    const h = await runningRun(t)
    await settle((await nextGet(t)).reply, snap({ seq: 2, phase: 'completed', outcome: 'completed_with_evidence', narrative: 'answer' }))
    expect(h.result.current.headMoved).toBe(false)

    h.rerender({ ws: fakeWorkspace({ scenario: scenarioAt(3) }) })
    expect(h.result.current.headMoved).toBe(false)

    h.rerender({ ws: fakeWorkspace({ scenario: scenarioAt(4) }) })
    expect(h.result.current.headMoved).toBe(true)
    expect(h.result.current.run?.scenario.revision).toBe(3)
    expect(h.result.current.run?.phase).toBe('completed')
    expect(h.result.current.run?.narrative).toBe('answer')

    h.rerender({ ws: fakeWorkspace({ scenario: scenarioAt(9, 'another-scenario') }) })
    expect(h.result.current.headMoved).toBe(false)
  })
})
