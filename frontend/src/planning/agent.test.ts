import { describe, expect, it } from 'vitest'
import type { AgentRun, AgentStatus } from '../api/types'
import { CanopyClient } from '../api/client'
import { availability, goalError, runView, uncitedRuns } from './agent'

// Labelled synthetic view-model inputs (shapes from generated/http.ts), not backend results.
const status = (over: Partial<AgentStatus> = {}): AgentStatus => ({
  configured: true, model: 'm', model_base_url: 'http://127.0.0.1:8000/v1', reachable: true, model_listed: true,
  listed_models: ['m'], allowed_operations: ['evaluate_layout'], active_run_id: null, reason: null,
  authority: 'Acceptance stays with the human.', ...over,
})
const run = (over: Partial<AgentRun> = {}): AgentRun => ({
  run_id: 'r1', status: 'completed', stop_requested: false, scenario_ref: { scenario_id: 's', revision: 1, scope: 'accepted' },
  goal: 'g', operations: ['evaluate_layout'], model: 'm', model_base_url: 'http://127.0.0.1:8000/v1', listed_models: ['m'],
  started_at_utc: '2026-11-13T00:00:00Z', finished_at_utc: '2026-11-13T00:00:10Z', elapsed_s: 10, model_completions: 2,
  format_repairs_used: 0, tool_calls: [], computed_run_ids: ['a'], evidence_ids: ['a'], cited_run_ids: ['a'],
  evidence_verified: true, authoritative_summary: 'x', untrusted_model_narrative: 'y', rejected_model_reply: null, reason: null, ...over,
})

describe('agent availability', () => {
  it('is unavailable until the server says a listed, reachable model is configured', () => {
    expect(availability(null, null).available).toBe(false)
    expect(availability(null, 'HTTP_503').tone).toBe('danger')
    expect(availability(status({ configured: false, model: null, reachable: null, model_listed: null }), null)).toMatchObject({ available: false, tone: 'muted' })
    expect(availability(status({ reachable: false, reason: 'refused' }), null)).toMatchObject({ available: false, tone: 'warning' })
    expect(availability(status({ model_listed: false, listed_models: ['other'] }), null).detail).toContain('other')
    expect(availability(status(), null)).toMatchObject({ available: true, tone: 'success' })
  })
})

describe('agent run view', () => {
  it('never presents a failed run as evidence and lists its computed runs as uncited', () => {
    const failed = run({ status: 'failed', reason: 'ProtocolError: unknown or malformed evidence IDs', computed_run_ids: ['a', 'b'], evidence_ids: [], cited_run_ids: [], evidence_verified: null, authoritative_summary: null, untrusted_model_narrative: null })
    expect(runView(failed).tone).toBe('danger')
    expect(runView(failed).detail).toContain('Nothing was accepted')
    expect(uncitedRuns(failed)).toEqual(['a', 'b'])
  })
  it('marks completed runs as backend evidence and reports only uncited extras', () => {
    expect(runView(run()).tone).toBe('success')
    expect(uncitedRuns(run({ computed_run_ids: ['a', 'c'] }))).toEqual(['c'])
  })
  it('shows a requested stop while the server finishes the current step', () => {
    expect(runView(run({ status: 'running', stop_requested: true })).title).toContain('Stopping')
  })
  it('validates the goal like the server (non-blank, at most 600 characters)', () => {
    expect(goalError('   ')).not.toBeNull()
    expect(goalError('x'.repeat(601))).not.toBeNull()
    expect(goalError('Evaluate')).toBeNull()
  })
})

describe('agent client', () => {
  it('only talks to the application API, never to a model endpoint', async () => {
    const calls: { url: string; method?: string; body?: unknown }[] = []
    const client = new CanopyClient('/api/v1', async (url, init) => {
      calls.push({ url, method: init?.method, body: init?.body })
      return new Response(JSON.stringify(run()), { status: 200 })
    })
    await client.agentStatus()
    await client.startAgentRun({ scenario_ref: { scenario_id: 's', revision: 1, scope: 'accepted' }, goal: 'g' })
    await client.agentRun('r/1')
    await client.stopAgentRun('r1')
    expect(calls.map(c => `${c.method} ${c.url}`)).toEqual([
      'GET /api/v1/agent/status', 'POST /api/v1/agent/runs', 'GET /api/v1/agent/runs/r%2F1', 'POST /api/v1/agent/runs/r1/stop',
    ])
    expect(calls.every(c => !c.url.includes('/v1/chat') && !c.url.includes(':8000'))).toBe(true)
  })
})
