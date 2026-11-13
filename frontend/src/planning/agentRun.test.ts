import { describe, expect, it } from 'vitest'
import {
  AGENT_TRANSPORT_UNAVAILABLE_REASON, MAX_QUESTION_LENGTH, applySnapshot, isReadableSnapshot, isTerminalPhase, supersededByHead, unavailableTransport,
  validateQuestion, type AgentRunPhase, type AgentRunSnapshot, type AgentRunView,
} from './agentRun'

// LABELLED SYNTHETIC TEST INPUT: hand-made run views and snapshots to exercise the pure reducer. They are not
// agent output, carry no computed figures and are never rendered by the application.
const view = (over: Partial<AgentRunView> = {}): AgentRunView => ({
  requestId: 'req-1', agentRunId: null, phase: 'submitting', question: 'synthetic question',
  scenario: { scenario_id: 's1', revision: 3, scope: 'accepted' }, selectedFeatureId: null,
  steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, lastSeq: 0, ...over,
})
const snap = (over: Partial<AgentRunSnapshot> = {}): AgentRunSnapshot => ({
  agentRunId: 'ar-1', seq: 1, phase: 'running', steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, ...over,
})

describe('validateQuestion', () => {
  it('trims and accepts ordinary text', () => {
    expect(validateQuestion('  where could a tree go?  ')).toEqual({ ok: true, question: 'where could a tree go?' })
  })
  it('rejects empty and whitespace-only text', () => {
    expect(validateQuestion('').ok).toBe(false)
    expect(validateQuestion('   \n\t ').ok).toBe(false)
  })
  it('accepts exactly the limit and rejects one character over, after trimming', () => {
    expect(validateQuestion('a'.repeat(MAX_QUESTION_LENGTH)).ok).toBe(true)
    expect(validateQuestion(`  ${'a'.repeat(MAX_QUESTION_LENGTH)}  `).ok).toBe(true)
    const over = validateQuestion('a'.repeat(MAX_QUESTION_LENGTH + 1))
    expect(over.ok).toBe(false)
    if (!over.ok) expect(over.reason).toMatch(/2000/)
    expect(MAX_QUESTION_LENGTH).toBe(2000)
  })
})

describe('isTerminalPhase', () => {
  it('is true only for completed, stopped and failed', () => {
    const phases: AgentRunPhase[] = ['submitting', 'running', 'stop_requested', 'completed', 'stopped', 'failed', 'status_unknown']
    expect(phases.filter(isTerminalPhase)).toEqual(['completed', 'stopped', 'failed'])
  })
})

describe('supersededByHead', () => {
  const run = view()
  it('is false without a head, or at the same or an older revision', () => {
    expect(supersededByHead(run, null)).toBe(false)
    expect(supersededByHead(run, { scenario_id: 's1', revision: 3, scope: 'accepted' })).toBe(false)
    expect(supersededByHead(run, { scenario_id: 's1', revision: 2, scope: 'accepted' })).toBe(false)
  })
  it('is true when the same scenario and scope moved to a later revision', () => {
    expect(supersededByHead(run, { scenario_id: 's1', revision: 4, scope: 'accepted' })).toBe(true)
  })
  it('is false for a different scenario or scope', () => {
    expect(supersededByHead(run, { scenario_id: 's2', revision: 9, scope: 'accepted' })).toBe(false)
    expect(supersededByHead(run, { scenario_id: 's1', revision: 9, scope: 'hypothetical' })).toBe(false)
  })
})

describe('applySnapshot', () => {
  it('adopts the agent run id and the server phase on the first reply', () => {
    const next = applySnapshot(view(), snap({ narrative: 'untrusted text', evidenceIds: ['job-1'], seq: 2 }))
    expect(next).toMatchObject({ requestId: 'req-1', agentRunId: 'ar-1', phase: 'running', narrative: 'untrusted text', evidenceIds: ['job-1'], lastSeq: 2 })
    expect(next.scenario).toEqual(view().scenario) // the run keeps the scenario it started against
  })
  it('ignores a snapshot for a different agent run', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'running', lastSeq: 1 })
    expect(applySnapshot(run, snap({ agentRunId: 'ar-other', seq: 9, phase: 'completed' }))).toBe(run)
  })
  it('ignores a stale snapshot (lower seq)', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'stop_requested', lastSeq: 5 })
    expect(applySnapshot(run, snap({ seq: 4, phase: 'running' }))).toBe(run)
  })
  it('re-applies an equal seq, so a re-check restores a known phase after status_unknown', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'status_unknown', lastSeq: 5, error: 'lost' })
    const next = applySnapshot(run, snap({ seq: 5, phase: 'running' }))
    expect(next.phase).toBe('running')
    expect(next.error).toBeNull()
    expect(next.lastSeq).toBe(5)
  })
  it('applies a terminal snapshot with its outcome and error verbatim', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'running', lastSeq: 1 })
    const done = applySnapshot(run, snap({ seq: 2, phase: 'completed', outcome: 'answered' }))
    expect(done.phase).toBe('completed')
    expect(done.outcome).toBe('answered')
    const failed = applySnapshot(run, snap({ seq: 2, phase: 'failed', error: 'tool refused' }))
    expect(failed).toMatchObject({ phase: 'failed', error: 'tool refused' })
  })
  it('never moves a terminal run back to a non-terminal phase', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'stopped', lastSeq: 3 })
    expect(applySnapshot(run, snap({ seq: 4, phase: 'running' }))).toBe(run)
    expect(applySnapshot(run, snap({ seq: 4, phase: 'stopped', outcome: 'stopped by user' })).outcome).toBe('stopped by user')
  })
  it('ignores a snapshot with a phase this client does not know', () => {
    const run = view({ agentRunId: 'ar-1', phase: 'running', lastSeq: 1 })
    expect(applySnapshot(run, snap({ seq: 2, phase: 'paused' as unknown as AgentRunSnapshot['phase'] }))).toBe(run)
  })
  it('ignores a first reply with an empty agent run id or a non-finite seq', () => {
    const run = view()
    expect(applySnapshot(run, snap({ agentRunId: '' }))).toBe(run)
    expect(applySnapshot(run, snap({ seq: Number.NaN }))).toBe(run)
  })
})

describe('isReadableSnapshot', () => {
  it('accepts a known phase with a run id and a finite seq, and rejects anything else', () => {
    expect(isReadableSnapshot(snap())).toBe(true)
    expect(isReadableSnapshot(snap({ phase: 'queued' as unknown as AgentRunSnapshot['phase'] }))).toBe(false)
    expect(isReadableSnapshot(snap({ agentRunId: '' }))).toBe(false)
    expect(isReadableSnapshot(snap({ seq: Number.POSITIVE_INFINITY }))).toBe(false)
    expect(isReadableSnapshot(null)).toBe(false)
    expect(isReadableSnapshot(undefined)).toBe(false)
  })
})

describe('unavailableTransport', () => {
  it('reports unavailable with the plain reason and refuses every run operation', async () => {
    await expect(unavailableTransport.status()).resolves.toEqual({ kind: 'unavailable', reason: AGENT_TRANSPORT_UNAVAILABLE_REASON })
    const req = { requestId: 'r', question: 'q', scenario: { scenario_id: 's', revision: 1, scope: 'accepted' }, selectedFeatureId: null }
    await expect(unavailableTransport.start(req)).rejects.toThrow(AGENT_TRANSPORT_UNAVAILABLE_REASON)
    await expect(unavailableTransport.get('x')).rejects.toThrow()
    await expect(unavailableTransport.cancel('x')).rejects.toThrow()
  })
  it('uses plain wording', () => {
    expect(AGENT_TRANSPORT_UNAVAILABLE_REASON).toMatch(/not connected/)
    expect(AGENT_TRANSPORT_UNAVAILABLE_REASON).not.toMatch(/optim|prove|verified|real site|measured shade/i)
  })
})
