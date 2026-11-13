// @vitest-environment jsdom
import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Scenario } from '../api/types'
import { AGENT_TRANSPORT_UNAVAILABLE_REASON, type AgentAvailability, type AgentRunSnapshot, type AgentRunTransport } from './agentRun'
import { useAgentRun, type AgentRunOptions } from './useAgentRun'
import type { Workspace } from './useWorkspace'

// LABELLED SYNTHETIC TEST INPUT: a fake transport whose every call waits until the test settles it, and a
// minimal fake Workspace. Snapshots are hand-made lifecycle states with no figures; they are not model output,
// not a backend contract and never rendered by the application. No agent-run API exists yet (#73).

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

const fakeWs = (over: { revision?: number; draftDirty?: boolean; noScenario?: boolean } = {}): Workspace => ({
  scenario: over.noScenario ? null : ({ scenario_id: 's1', revision: over.revision ?? 1, scope: 'accepted' } as unknown as Scenario),
  draftDirty: over.draftDirty ?? false,
  editPending: false,
} as unknown as Workspace)

const OPTIONS: AgentRunOptions = { pollMs: 5, requestTimeoutMs: 0 }
const settle = () => act(async () => { await new Promise(r => setTimeout(r, 30)) })

function setup(transport: AgentRunTransport, ws: Workspace = fakeWs(), options: AgentRunOptions = OPTIONS) {
  let n = 0
  const opts = { ...options, newRequestId: () => `req-${++n}` }
  return renderHook(({ w }) => useAgentRun(w, transport, opts), { initialProps: { w: ws } })
}

async function ready(transport: AgentRunTransport, ws?: Workspace, options?: AgentRunOptions) {
  const hook = setup(transport, ws, options)
  await waitFor(() => expect(hook.result.current.availability).not.toBeNull())
  return hook
}

describe('useAgentRun', () => {
  it('defaults to the unavailable transport: not connected, cannot submit, submit does nothing', async () => {
    const { result } = renderHook(() => useAgentRun(fakeWs()))
    expect(result.current.availability).toBeNull()
    expect(result.current.canSubmit).toBe(false)
    await waitFor(() => expect(result.current.availability?.kind).toBe('unavailable'))
    expect(result.current.blockedReason).toBe(AGENT_TRANSPORT_UNAVAILABLE_REASON)
    act(() => result.current.submit('anything'))
    expect(result.current.run).toBeNull()
  })

  it('submits one run against the accepted head and follows it to completed, then stops polling', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    expect(result.current.canSubmit).toBe(true)
    expect(result.current.blockedReason).toBeNull()
    act(() => result.current.submit('  where could one more tree go?  '))
    expect(result.current.run).toMatchObject({ phase: 'submitting', requestId: 'req-1', agentRunId: null, question: 'where could one more tree go?', scenario: { scenario_id: 's1', revision: 1, scope: 'accepted' } })
    expect(result.current.canSubmit).toBe(false)
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    expect(f.of('start')[0].arg).toMatchObject({ requestId: 'req-1', question: 'where could one more tree go?', selectedFeatureId: null })
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    expect(result.current.run).toMatchObject({ phase: 'running', agentRunId: 'ar-1', lastSeq: 1 })
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    expect(f.of('get')[0].arg).toBe('ar-1')
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2, steps: [{ seq: 1, tool: 'evaluate_layout', status: 'running', jobId: 'j1', runId: null, error: null }] })))
    expect(result.current.run?.steps[0].tool).toBe('evaluate_layout')
    await waitFor(() => expect(f.of('get')).toHaveLength(2))
    await act(async () => f.of('get')[1].resolve(snap({ seq: 3, phase: 'completed', outcome: 'answered', narrative: 'untrusted', evidenceIds: ['j1'] })))
    expect(result.current.run).toMatchObject({ phase: 'completed', outcome: 'answered', narrative: 'untrusted', evidenceIds: ['j1'] })
    await settle()
    expect(f.of('get')).toHaveLength(2) // terminal: no more polling
    expect(result.current.canSubmit).toBe(true)
  })

  it('ignores a duplicate submit while the first is in flight, even in the same tick', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => { result.current.submit('first'); result.current.submit('second') })
    act(() => result.current.submit('third'))
    await settle()
    expect(f.of('start')).toHaveLength(1)
    expect(result.current.run?.question).toBe('first')
  })

  it('start() rejects -> status_unknown, saying it may or may not have reached the server; recheck re-sends the same requestId', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].reject(new Error('connection reset')))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.run?.error).toMatch(/may or may not have reached the server/)
    expect(result.current.run?.error).toMatch(/connection reset/)
    expect(result.current.canSubmit).toBe(false)
    expect(result.current.blockedReason).toMatch(/unknown/)
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('start')).toHaveLength(2))
    expect(f.of('start')[1].arg).toEqual(f.of('start')[0].arg) // same requestId, question and scenario
    expect((f.of('start')[1].arg as { requestId: string }).requestId).toBe('req-1')
    expect(result.current.run?.phase).toBe('status_unknown') // a re-sent start is not presented as certain
    await act(async () => f.of('start')[1].resolve(snap({ seq: 1 })))
    expect(result.current.run).toMatchObject({ phase: 'running', agentRunId: 'ar-1', requestId: 'req-1', error: null })
  })

  it('a start() reply with an unknown phase becomes status_unknown (not stuck submitting); recheck re-sends the same requestId; clear works', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1, phase: 'queued' as unknown as AgentRunSnapshot['phase'] })))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.run?.agentRunId).toBeNull()
    expect(result.current.run?.error).toMatch(/could not be read/)
    expect(result.current.run?.error).toMatch(/may or may not have started/)
    expect(result.current.run?.error).not.toMatch(/optim|prove|verified|real site|measured shade/i)
    expect(result.current.blockedReason).toMatch(/unknown/)
    await settle()
    expect(f.of('get')).toHaveLength(0) // nothing to poll without a run id
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('start')).toHaveLength(2))
    expect((f.of('start')[1].arg as { requestId: string }).requestId).toBe('req-1')
    await act(async () => f.of('start')[1].resolve(snap({ seq: 1 })))
    expect(result.current.run).toMatchObject({ phase: 'running', agentRunId: 'ar-1', error: null })

    const g = fakeTransport()
    const other = await ready(g.transport)
    act(() => other.result.current.submit('q'))
    await waitFor(() => expect(g.of('start')).toHaveLength(1))
    await act(async () => g.of('start')[0].resolve(snap({ seq: 1, phase: 'queued' as unknown as AgentRunSnapshot['phase'] })))
    act(() => other.result.current.clear())
    expect(other.result.current.run).toBeNull()
    expect(other.result.current.canSubmit).toBe(true)
  })

  it('a start() reply with an empty run id or a negative seq becomes status_unknown', async () => {
    for (const bad of [snap({ agentRunId: '' }), snap({ seq: -1 })]) {
      const f = fakeTransport()
      const { result } = await ready(f.transport)
      act(() => result.current.submit('q'))
      await waitFor(() => expect(f.of('start')).toHaveLength(1))
      await act(async () => f.of('start')[0].resolve(bad))
      expect(result.current.run?.phase).toBe('status_unknown')
      expect(result.current.run?.agentRunId).toBeNull()
      await settle()
      expect(f.of('get')).toHaveLength(0)
    }
  })

  it('a get() reply with an unknown phase becomes status_unknown and polling stops; recheck resumes with get()', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].resolve(snap({ seq: 2, phase: 'paused' as unknown as AgentRunSnapshot['phase'] })))
    expect(result.current.run).toMatchObject({ phase: 'status_unknown', agentRunId: 'ar-1', lastSeq: 1 })
    expect(result.current.run?.error).toMatch(/could not be read/)
    await settle()
    expect(f.of('get')).toHaveLength(1)
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('get')).toHaveLength(2))
    expect(f.of('start')).toHaveLength(1)
  })

  it('get() rejects -> status_unknown (never failed, never running) and polling stops; recheck resumes with get()', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].reject(new Error('timeout')))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.run?.error).toMatch(/may still be running/)
    await settle()
    expect(f.of('get')).toHaveLength(1) // polling stopped
    expect(f.of('start')).toHaveLength(1)
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('get')).toHaveLength(2))
    expect(f.of('start')).toHaveLength(1) // a known run is re-queried, never re-started
    await act(async () => f.of('get')[1].resolve(snap({ seq: 2 })))
    expect(result.current.run?.phase).toBe('running')
    await waitFor(() => expect(f.of('get')).toHaveLength(3)) // polling resumed
  })

  it('drops out-of-order snapshots older than the last applied seq', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 5, narrative: 'newer' })))
    await waitFor(() => expect(f.of('get')).toHaveLength(1))
    await act(async () => f.of('get')[0].resolve(snap({ seq: 3, narrative: 'older' })))
    expect(result.current.run).toMatchObject({ lastSeq: 5, narrative: 'newer', phase: 'running' })
    await waitFor(() => expect(f.of('get')).toHaveLength(2)) // still running, so still polling
    await act(async () => f.of('get')[1].resolve(snap({ agentRunId: 'ar-foreign', seq: 9, phase: 'completed' })))
    expect(result.current.run).toMatchObject({ agentRunId: 'ar-1', phase: 'running', lastSeq: 5 })
  })

  it('drops a late reply after clear(), and a cleared run is not replaced by it', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].reject(new Error('lost')))
    act(() => result.current.recheck())
    await waitFor(() => expect(f.of('start')).toHaveLength(2))
    act(() => result.current.clear())
    expect(result.current.run).toBeNull()
    await act(async () => f.of('start')[1].resolve(snap({ seq: 1 })))
    await settle()
    expect(result.current.run).toBeNull()
    expect(f.of('get')).toHaveLength(0)
    expect(result.current.canSubmit).toBe(true)
  })

  it('clear() does nothing while a run is still running', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    act(() => result.current.clear())
    expect(result.current.run?.phase).toBe('running')
  })

  it('stop -> cancel(); shows the server phase stop_requested, then stopped', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    act(() => result.current.stop())
    await waitFor(() => expect(f.of('cancel')).toHaveLength(1))
    expect(f.of('cancel')[0].arg).toBe('ar-1')
    expect(result.current.run?.phase).toBe('running') // the server has not answered yet
    await act(async () => f.of('cancel')[0].resolve(snap({ seq: 2, phase: 'stop_requested' })))
    expect(result.current.run?.phase).toBe('stop_requested')
    expect(result.current.canSubmit).toBe(false)
    await waitFor(() => expect(f.of('get').length).toBeGreaterThanOrEqual(1))
    await act(async () => f.of('get')[f.of('get').length - 1].resolve(snap({ seq: 3, phase: 'stopped' })))
    expect(result.current.run?.phase).toBe('stopped')
    expect(result.current.canSubmit).toBe(true)
  })

  it('a rejected cancel() sets status_unknown', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport)
    act(() => result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    act(() => result.current.stop())
    await waitFor(() => expect(f.of('cancel')).toHaveLength(1))
    await act(async () => f.of('cancel')[0].reject(new Error('refused')))
    expect(result.current.run?.phase).toBe('status_unknown')
    expect(result.current.run?.error).toMatch(/stop request may or may not have reached the server/)
  })

  it('a hung start() times out into status_unknown', async () => {
    const f = fakeTransport()
    const { result } = await ready(f.transport, fakeWs(), { pollMs: 5, requestTimeoutMs: 20 })
    act(() => result.current.submit('q'))
    await waitFor(() => expect(result.current.run?.phase).toBe('status_unknown'))
    expect(result.current.run?.error).toMatch(/no reply/)
  })

  it('headMoved when the accepted head advances past the run; the answer is kept, not dropped', async () => {
    const f = fakeTransport()
    const hook = await ready(f.transport)
    act(() => hook.result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1, phase: 'completed', narrative: 'kept' })))
    expect(hook.result.current.headMoved).toBe(false)
    hook.rerender({ w: fakeWs({ revision: 2 }) })
    expect(hook.result.current.headMoved).toBe(true)
    expect(hook.result.current.run).toMatchObject({ narrative: 'kept', scenario: { revision: 1 } })
  })

  it('canSubmit is false with a draft, with no scenario, and while a run is non-terminal', async () => {
    const f = fakeTransport()
    const draft = await ready(f.transport, fakeWs({ draftDirty: true }))
    expect(draft.result.current.canSubmit).toBe(false)
    expect(draft.result.current.blockedReason).toMatch(/not accepted/)
    act(() => draft.result.current.submit('q'))
    expect(draft.result.current.run).toBeNull()

    const none = await ready(f.transport, fakeWs({ noScenario: true }))
    expect(none.result.current.canSubmit).toBe(false)
    expect(none.result.current.blockedReason).toMatch(/No accepted scenario/)

    const busy = await ready(f.transport)
    act(() => busy.result.current.submit('q'))
    expect(busy.result.current.canSubmit).toBe(false)
    expect(busy.result.current.blockedReason).toMatch(/in progress/)
    await waitFor(() => expect(f.of('start')).toHaveLength(1)) // only this hook's submit reached the transport
    await settle()
    expect(f.of('start')).toHaveLength(1)
  })

  it('stops polling on unmount', async () => {
    const f = fakeTransport()
    const hook = await ready(f.transport)
    act(() => hook.result.current.submit('q'))
    await waitFor(() => expect(f.of('start')).toHaveLength(1))
    await act(async () => f.of('start')[0].resolve(snap({ seq: 1 })))
    hook.unmount()
    await settle()
    expect(f.of('get')).toHaveLength(0)
  })

  it('user-visible reasons avoid forbidden wording', async () => {
    const f = fakeTransport()
    const hook = await ready(f.transport, fakeWs({ draftDirty: true }))
    const texts = [hook.result.current.blockedReason ?? '']
    hook.rerender({ w: fakeWs({ noScenario: true }) })
    texts.push(hook.result.current.blockedReason ?? '')
    for (const t of texts) expect(t).not.toMatch(/optim|prove|verified|real site|measured shade/i)
  })
})
