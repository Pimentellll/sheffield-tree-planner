// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Scenario } from '../api/types'
import {
  AGENT_RUN_STORAGE_KEY, AGENT_RUN_STORAGE_VERSION, RESTORED_RUN_NOTE, decodeStoredRun, encodeStoredRun, restoredRunView,
  type AgentAvailability, type AgentRunSnapshot, type AgentRunTransport, type StoredAgentRun,
} from './agentRun'
import { useAgentRun, type AgentRunOptions } from './useAgentRun'
import type { Workspace } from './useWorkspace'

// LABELLED SYNTHETIC TEST INPUT: a fake transport whose every call waits until the test settles it, a minimal
// fake Workspace, and hand-written session-storage records. Snapshots are hand-made lifecycle states with no
// figures; they are not model output and not a backend contract. No agent-run API exists yet (#73).

interface Pending {
  readonly kind: 'start' | 'get' | 'cancel'
  readonly arg: unknown
  resolve(snap: AgentRunSnapshot): void
  reject(err: Error): void
}

function fakeTransport(availability: AgentAvailability = { kind: 'available', model: 'synthetic-model' }) {
  const calls: Pending[] = []
  const pending = (kind: Pending['kind'], arg: unknown) =>
    new Promise<AgentRunSnapshot>((resolve, reject) => { calls.push({ kind, arg, resolve, reject }) })
  const transport: AgentRunTransport = {
    status: async () => availability,
    start: req => pending('start', req),
    get: id => pending('get', id),
    cancel: id => pending('cancel', id),
  }
  return { transport, calls, of: (kind: Pending['kind']) => calls.filter(c => c.kind === kind) }
}

const snap = (over: Partial<AgentRunSnapshot> = {}): AgentRunSnapshot => ({
  agentRunId: 'ar-1', seq: 1, phase: 'running', steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, ...over,
})

const fakeWs = (revision = 1): Workspace => ({
  scenario: { scenario_id: 's1', revision, scope: 'accepted' } as unknown as Scenario,
  draftDirty: false,
  editPending: false,
} as unknown as Workspace)

const OPTIONS: AgentRunOptions = { pollMs: 5, requestTimeoutMs: 0 }
const settle = () => act(async () => { await new Promise(r => setTimeout(r, 30)) })

function setup(transport: AgentRunTransport, ws: Workspace = fakeWs(), options: AgentRunOptions = OPTIONS) {
  let n = 0
  const opts = { ...options, newRequestId: () => `req-new-${++n}` }
  return renderHook(({ w }) => useAgentRun(w, transport, opts), { initialProps: { w: ws } })
}
async function ready(transport: AgentRunTransport, ws?: Workspace, options?: AgentRunOptions) {
  const hook = setup(transport, ws, options)
  await waitFor(() => expect(hook.result.current.availability).not.toBeNull())
  return hook
}

const RECORD: StoredAgentRun = {
  requestId: 'req-stored', agentRunId: 'ar-1', question: 'where could one more tree go?',
  scenario: { scenario_id: 's1', revision: 1, scope: 'accepted' }, selectedFeatureId: null,
}
const store = (record: StoredAgentRun) => sessionStorage.setItem(AGENT_RUN_STORAGE_KEY, encodeStoredRun(record))
const storedNow = () => decodeStoredRun(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY))

afterEach(() => { cleanup(); vi.restoreAllMocks(); sessionStorage.clear() })

describe('stored agent run record (pure)', () => {
  it('round-trips exactly the stored fields and nothing the server reported', () => {
    const view = { ...restoredRunView(RECORD), phase: 'running' as const, narrative: 'untrusted text', outcome: 'answered', lastSeq: 7 }
    const text = encodeStoredRun(view)
    expect(decodeStoredRun(text)).toEqual(RECORD)
    expect(Object.keys(JSON.parse(text)).sort()).toEqual(['agentRunId', 'question', 'requestId', 'scenario', 'selectedFeatureId', 'version'])
    expect(text).not.toContain('untrusted text')
    expect(text).not.toContain('answered')
  })

  it('a restored view is status_unknown with no steps, narrative, evidence or outcome', () => {
    expect(restoredRunView(RECORD)).toEqual({
      ...RECORD, phase: 'status_unknown', steps: [], narrative: null, evidenceIds: [], outcome: null, error: RESTORED_RUN_NOTE, lastSeq: 0,
    })
  })

  it('rejects anything that is not exactly a record of this version', () => {
    const good = { version: AGENT_RUN_STORAGE_VERSION, ...RECORD }
    const bad: unknown[] = [
      null, '', 'not json', '[]', '"text"', '42',
      { ...good, version: AGENT_RUN_STORAGE_VERSION + 1 }, { ...good, version: undefined }, { ...good, version: '1' },
      { ...good, requestId: '' }, { ...good, requestId: 7 }, { ...good, requestId: 'x'.repeat(201) },
      { ...good, agentRunId: '' }, { ...good, agentRunId: 3 }, { ...good, agentRunId: undefined },
      { ...good, question: '' }, { ...good, question: '  padded  ' }, { ...good, question: 'q'.repeat(2001) }, { ...good, question: null },
      { ...good, scenario: null }, { ...good, scenario: [] }, { ...good, scenario: { ...RECORD.scenario, revision: '1' } },
      { ...good, scenario: { ...RECORD.scenario, revision: null } }, { ...good, scenario: { ...RECORD.scenario, scenario_id: '' } },
      { ...good, scenario: { ...RECORD.scenario, scope: 5 } },
      { ...good, selectedFeatureId: 5 }, { ...good, selectedFeatureId: '' }, { ...good, selectedFeatureId: undefined },
    ]
    for (const value of bad) {
      const raw = typeof value === 'string' || value === null ? value : JSON.stringify(value)
      expect({ raw, decoded: decodeStoredRun(raw as string | null) }).toEqual({ raw, decoded: null })
    }
    expect(decodeStoredRun(JSON.stringify({ ...good, agentRunId: null, selectedFeatureId: 'tree-7' }))).toEqual({ ...RECORD, agentRunId: null, selectedFeatureId: 'tree-7' })
  })
})

describe('useAgentRun: finding a run again after a reload or remount', () => {
  it('writes the record on submit, adds the run id when it arrives, and stores nothing the server said', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
    act(() => result.current.submit('q one'))
    expect(storedNow()).toEqual({ requestId: 'req-new-1', agentRunId: null, question: 'q one', scenario: { scenario_id: 's1', revision: 1, scope: 'accepted' }, selectedFeatureId: null })
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1, narrative: 'untrusted model text', steps: [{ seq: 1, tool: 'evaluate_layout', status: 'running', jobId: 'j1', runId: null, error: null }] })))
    expect(storedNow()).toMatchObject({ requestId: 'req-new-1', agentRunId: 'ar-1' })
    const raw = sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)!
    expect(raw).not.toContain('untrusted model text')
    expect(raw).not.toContain('evaluate_layout')
    expect(raw).not.toContain('running')
  })

  it('restore with a run id: status_unknown at once, then get(); only the reply sets phase and steps', async () => {
    // Extra fields a tampered or foreign record might carry are ignored: stored data never says a run is going.
    sessionStorage.setItem(AGENT_RUN_STORAGE_KEY, JSON.stringify({ ...JSON.parse(encodeStoredRun(RECORD)), phase: 'completed', narrative: 'stored text', steps: [{ seq: 1 }], outcome: 'answered' }))
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    expect(result.current.run).toEqual(restoredRunView(RECORD))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.canSubmit).toBe(false)
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    expect(f.of('get')[0].arg).toBe('ar-1')
    expect(f.of('start')).toHaveLength(0)
    await act(async () => f.of('get')[0].resolve(snap({ seq: 4, steps: [{ seq: 1, tool: 'evaluate_layout', status: 'completed', jobId: 'j1', runId: 'r1', error: null }] })))
    expect(result.current.run).toMatchObject({ phase: 'running', requestId: 'req-stored', agentRunId: 'ar-1', lastSeq: 4, error: null, narrative: null })
    expect(result.current.run?.steps).toHaveLength(1)
    await waitFor(() => expect(f.of('get')).toHaveLength(2)) // polling resumed
    await act(async () => f.of('get')[1].resolve(snap({ seq: 5, phase: 'completed', outcome: 'answered' })))
    expect(result.current.run?.phase).toBe('completed')
    expect(f.of('start')).toHaveLength(0)
  })

  it('restore without a run id: start() is re-sent once with the same request id, and no second run is made', async () => {
    store({ ...RECORD, agentRunId: null, selectedFeatureId: 'tree-7' })
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    expect(result.current.run).toMatchObject({ phase: 'status_unknown', requestId: 'req-stored', agentRunId: null })
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    expect(f.of('start')[0].arg).toEqual({ requestId: 'req-stored', question: RECORD.question, scenario: RECORD.scenario, selectedFeatureId: 'tree-7' })
    expect(f.of('get')).toHaveLength(0)
    expect(result.current.run?.phase).toBe('status_unknown') // not presented as running until the server answers
    act(() => result.current.submit('a different question')) // blocked: one run at a time
    await settle()
    expect(f.of('start')).toHaveLength(1)
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    expect(result.current.run).toMatchObject({ phase: 'running', requestId: 'req-stored', agentRunId: 'ar-1' })
    expect(storedNow()).toMatchObject({ requestId: 'req-stored', agentRunId: 'ar-1' })
    expect(f.of('start')).toHaveLength(1)
  })

  it('a lost reply after restore leaves status_unknown (never failed or running); recheck asks again', async () => {
    store(RECORD)
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].reject(new Error('connection reset')))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.run?.error).toMatch(/could not be read/)
    expect(result.current.run?.error).toMatch(/connection reset/)
    expect(storedNow()).toEqual(RECORD) // still findable
    await settle()
    expect(f.of('get')).toHaveLength(1) // an unknown run is not polled
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('get')).toHaveLength(2))
    await act(async () => f.of('get')[1].resolve(snap({ seq: 2 })))
    expect(result.current.run?.phase).toBe('running')
  })

  it('a reply that times out after restore also leaves status_unknown', async () => {
    store({ ...RECORD, agentRunId: null })
    const f = fakeTransport()
    const { result } = await ready(f.transport, fakeWs(), { pollMs: 5, requestTimeoutMs: 20 })
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await waitFor(() => expect(result.current.run?.error).toMatch(/no reply within/))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(storedNow()).toMatchObject({ requestId: 'req-stored', agentRunId: null })
  })

  it('stop after restore calls cancel() with the stored run id; the stopped run removes the record', async () => {
    store(RECORD)
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.stop()) // not yet: its status is unknown
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    expect(f.of('cancel')).toHaveLength(0)
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2 })))
    act(() => result.current.stop())
    await waitFor(() => expect(f.of('cancel')).toHaveLength(1))
    expect(f.of('cancel')[0].arg).toBe('ar-1')
    await act(async () => f.of('cancel')[0].resolve(snap({ seq: 3, phase: 'stopped', outcome: 'stopped' })))
    expect(result.current.run?.phase).toBe('stopped')
    expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
  })

  it('a terminal phase removes the record, so a later mount restores nothing', async () => {
    const f = fakeTransport()
    const first = await ready(f.transport)
    act(() => first.result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    expect(storedNow()).not.toBeNull()
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2, phase: 'failed', error: 'synthetic failure' })))
    expect(first.result.current.run?.phase).toBe('failed')
    expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
    first.unmount()
    const g = fakeTransport()
    const second = await ready(g.transport)
    await settle()
    expect(second.result.current.run).toBeNull()
    expect(g.calls).toHaveLength(0)
  })

  it('clear() removes the record', async () => {
    store(RECORD)
    const f = fakeTransport()
    const first = await ready(f.transport)
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    act(() => first.result.current.clear())
    expect(first.result.current.run).toBeNull()
    expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2 }))) // late reply for the cleared run
    expect(first.result.current.run).toBeNull()
    expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
    first.unmount()
    const g = fakeTransport()
    const second = await ready(g.transport)
    await settle()
    expect(second.result.current.run).toBeNull()
    expect(g.calls).toHaveLength(0)
  })

  it('a malformed or other-version record is ignored and removed, whatever the transport says', async () => {
    const cases = [
      'not json',
      JSON.stringify({ ...RECORD, version: AGENT_RUN_STORAGE_VERSION + 1 }),
      JSON.stringify({ ...RECORD }), // no version
      JSON.stringify({ version: AGENT_RUN_STORAGE_VERSION, ...RECORD, scenario: { scenario_id: 's1' } }),
    ]
    const availabilities: AgentAvailability[] = [{ kind: 'available', model: null }, { kind: 'unavailable', reason: 'synthetic: off' }]
    for (const raw of cases) {
      for (const availability of availabilities) {
        sessionStorage.setItem(AGENT_RUN_STORAGE_KEY, raw)
        const f = fakeTransport(availability)
        const hook = await ready(f.transport)
        await settle()
        expect(hook.result.current.run).toBeNull()
        expect(f.calls).toHaveLength(0)
        expect(sessionStorage.getItem(AGENT_RUN_STORAGE_KEY)).toBeNull()
        if (availability.kind === 'available') expect(hook.result.current.canSubmit).toBe(true)
        hook.unmount()
      }
    }
  })

  it('storage that throws does not break mount, submit, polling or clear', async () => {
    const boom = () => { throw new Error('synthetic: storage blocked') }
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(boom)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(boom)
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(boom)
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    expect(result.current.run).toBeNull()
    expect(result.current.canSubmit).toBe(true)
    act(() => result.current.submit('q'))
    expect(result.current.run?.phase).toBe('submitting')
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    expect(result.current.run?.phase).toBe('running')
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2, phase: 'completed' })))
    expect(result.current.run?.phase).toBe('completed')
    act(() => result.current.clear())
    expect(result.current.run).toBeNull()
  })

  it('a restored run started against an older accepted revision is labelled like a live one', async () => {
    store(RECORD) // revision 1
    const f = fakeTransport()
    const { result, rerender } = await ready(f.transport, fakeWs(2))
    expect(result.current.run?.scenario.revision).toBe(1)
    expect(result.current.headMoved).toBe(true)
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2, phase: 'completed', outcome: 'answered' })))
    expect(result.current.run).toMatchObject({ phase: 'completed', scenario: { revision: 1 } })
    expect(result.current.headMoved).toBe(true)
    rerender({ w: fakeWs(1) })
    expect(result.current.headMoved).toBe(false)
  })

  it('unavailable transport after reload: nothing is shown or sent, and the record is kept', async () => {
    store(RECORD)
    const f = fakeTransport({ kind: 'unavailable', reason: 'synthetic: agent off' })
    const { result } = await ready(f.transport)
    await settle()
    expect(result.current.run).toBeNull()
    expect(result.current.canSubmit).toBe(false)
    expect(result.current.blockedReason).toBe('synthetic: agent off')
    expect(f.calls).toHaveLength(0)
    expect(storedNow()).toEqual(RECORD)
  })

  it('the default (unavailable) transport leaves a stored record alone', async () => {
    store(RECORD)
    const { result } = renderHook(() => useAgentRun(fakeWs()))
    await waitFor(() => expect(result.current.availability?.kind).toBe('unavailable'))
    expect(result.current.run).toBeNull()
    expect(storedNow()).toEqual(RECORD)
  })

  it('unmount then remount (the panel closing and reopening) finds the same run and starts no second one', async () => {
    const f = fakeTransport()
    const first = await ready(f.transport)
    act(() => first.result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    expect(first.result.current.run?.phase).toBe('running')
    first.unmount()
    expect(storedNow()).toMatchObject({ requestId: 'req-new-1', agentRunId: 'ar-1' })
    const g = fakeTransport()
    const second = await ready(g.transport)
    expect(second.result.current.run).toMatchObject({ phase: 'status_unknown', requestId: 'req-new-1', agentRunId: 'ar-1', question: 'q' })
    await waitFor(() => expect(g.of('get')).toHaveLength(1))
    expect(g.of('start')).toHaveLength(0)
    await act(async () => g.of('get')[0].resolve(snap({ seq: 3, phase: 'stop_requested' })))
    expect(second.result.current.run?.phase).toBe('stop_requested')
  })
})
