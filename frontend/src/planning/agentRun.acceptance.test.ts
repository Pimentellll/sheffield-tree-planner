import { describe, expect, it } from 'vitest'
import {
  AGENT_TRANSPORT_UNAVAILABLE_REASON, applySnapshot, isTerminalPhase, supersededByHead, unavailableTransport, validateQuestion,
  type AgentRunPhase, type AgentRunSnapshot, type AgentRunView, type AgentScenarioKey,
} from './agentRun'

// Independent acceptance tests for the pure agent-run module, written from the shared interface and
// behaviour rules only (not from the implementation). LABELLED SYNTHETIC TEST INPUTS: the snapshots
// and runs below are hand-made frontend-normalised shapes, not agent-run wire data, model output or
// runtime results. No agent-run API exists in this build (#73 unpublished).

const FORBIDDEN = [/\boptimal\b/i, /\boptimi[sz]/i, /\bprove[ns]?\b|\bproving\b/i, /\bverified\b/i, /\breal site\b/i, /\bmeasured shade\b/i]
const forbiddenIn = (text: string) => FORBIDDEN.filter(re => re.test(text)).map(String)

const key: AgentScenarioKey = { scenario_id: 's1', revision: 3, scope: 'accepted' }
const run = (over: Partial<AgentRunView> = {}): AgentRunView => ({
  requestId: 'req-1', agentRunId: null, phase: 'submitting', question: 'Evaluate the proposed planting layout', scenario: key,
  selectedFeatureId: null, steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, lastSeq: 0, ...over,
})
const snap = (over: Partial<AgentRunSnapshot> = {}): AgentRunSnapshot => ({
  agentRunId: 'ar-1', seq: 1, phase: 'running', steps: [], narrative: null, evidenceIds: [], outcome: null, error: null, ...over,
})

describe('agentRun acceptance: unavailable transport (no agent-run API in this build)', () => {
  it('status() resolves unavailable with the one honest reason; start/get/cancel reject', async () => {
    await expect(unavailableTransport.status()).resolves.toEqual({ kind: 'unavailable', reason: AGENT_TRANSPORT_UNAVAILABLE_REASON })
    await expect(unavailableTransport.start({ requestId: 'r', question: 'q', scenario: key, selectedFeatureId: null })).rejects.toBeDefined()
    await expect(unavailableTransport.get('ar-1')).rejects.toBeDefined()
    await expect(unavailableTransport.cancel('ar-1')).rejects.toBeDefined()
  })

  it('the reason is a plain non-empty sentence that claims nothing it cannot show', () => {
    expect(AGENT_TRANSPORT_UNAVAILABLE_REASON.trim().length).toBeGreaterThan(10)
    expect(AGENT_TRANSPORT_UNAVAILABLE_REASON).toMatch(/agent/i)
    expect(forbiddenIn(AGENT_TRANSPORT_UNAVAILABLE_REASON)).toEqual([])
  })
})

describe('agentRun acceptance: isTerminalPhase', () => {
  it('only completed, stopped and failed are terminal; status_unknown is not', () => {
    const all: AgentRunPhase[] = ['submitting', 'running', 'stop_requested', 'completed', 'stopped', 'failed', 'status_unknown']
    expect(all.filter(isTerminalPhase)).toEqual(['completed', 'stopped', 'failed'])
  })
})

describe('agentRun acceptance: supersededByHead (revision and currentness)', () => {
  const r = run({ agentRunId: 'ar-1', phase: 'completed', lastSeq: 2 })
  it('is true only when the same scenario and scope advance past the run revision', () => {
    expect(supersededByHead(r, { scenario_id: 's1', revision: 4, scope: 'accepted' })).toBe(true)
    expect(supersededByHead(r, { scenario_id: 's1', revision: 3, scope: 'accepted' })).toBe(false)
    expect(supersededByHead(r, { scenario_id: 's1', revision: 2, scope: 'accepted' })).toBe(false)
  })
  it('is false for a different scenario_id, a different scope or no head', () => {
    expect(supersededByHead(r, { scenario_id: 'other', revision: 9, scope: 'accepted' })).toBe(false)
    expect(supersededByHead(r, { scenario_id: 's1', revision: 9, scope: 'hypothetical' })).toBe(false)
    expect(supersededByHead(r, null)).toBe(false)
  })
})

describe('agentRun acceptance: applySnapshot (late and out-of-order replies)', () => {
  it('applies the server phase and fields, adopts the agentRunId and keeps the request identity', () => {
    const steps = [{ seq: 1, tool: 'evaluate_layout', status: 'running' as const, jobId: 'job-1', runId: null, error: null }]
    const next = applySnapshot(run(), snap({ seq: 1, phase: 'running', steps, narrative: 'n', evidenceIds: ['job-1'], outcome: null }))
    expect(next.agentRunId).toBe('ar-1')
    expect(next.phase).toBe('running')
    expect(next.steps).toEqual(steps)
    expect(next.narrative).toBe('n')
    expect(next.evidenceIds).toEqual(['job-1'])
    expect(next.lastSeq).toBe(1)
    expect([next.requestId, next.question, next.scenario, next.selectedFeatureId]).toEqual(['req-1', 'Evaluate the proposed planting layout', key, null])
    const done = applySnapshot(next, snap({ seq: 2, phase: 'completed', outcome: 'completed_with_evidence', error: null }))
    expect([done.phase, done.outcome, done.lastSeq]).toEqual(['completed', 'completed_with_evidence', 2])
  })

  it('an older seq arriving after a newer one changes nothing', () => {
    const newer = run({ agentRunId: 'ar-1', phase: 'running', narrative: 'newer', lastSeq: 5 })
    const after = applySnapshot(newer, snap({ seq: 4, phase: 'completed', narrative: 'older', outcome: 'x' }))
    expect(after).toEqual(newer)
  })

  it('a snapshot for a different agentRunId than the known one changes nothing', () => {
    const known = run({ agentRunId: 'ar-1', phase: 'running', lastSeq: 1 })
    expect(applySnapshot(known, snap({ agentRunId: 'ar-2', seq: 9, phase: 'completed' }))).toEqual(known)
  })

  it('a newer server snapshot recovers a run whose status was unknown, with the server phase', () => {
    const unknown = run({ agentRunId: 'ar-1', phase: 'status_unknown', error: 'network down', lastSeq: 2 })
    const back = applySnapshot(unknown, snap({ seq: 3, phase: 'stopped' }))
    expect([back.phase, back.lastSeq]).toEqual(['stopped', 3])
  })
})

describe('agentRun acceptance: validateQuestion', () => {
  it('trims and accepts up to 2000 characters', () => {
    expect(validateQuestion('  Evaluate the layout  ')).toEqual({ ok: true, question: 'Evaluate the layout' })
    const max = 'a'.repeat(2000)
    expect(validateQuestion(max)).toEqual({ ok: true, question: max })
    expect(validateQuestion(`  ${max}  `)).toEqual({ ok: true, question: max })
  })
  it('rejects empty, whitespace-only and over-length text with a plain reason', () => {
    for (const bad of ['', '   \n\t ', 'a'.repeat(2001)]) {
      const v = validateQuestion(bad)
      expect(v.ok).toBe(false)
      if (!v.ok) {
        expect(v.reason.trim().length).toBeGreaterThan(0)
        expect(forbiddenIn(v.reason)).toEqual([])
      }
    }
  })
})
