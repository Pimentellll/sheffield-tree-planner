import { useEffect, useRef, useState } from 'react'
import type { M2Session } from '../../../generated/contracts'
import type { Job, Result } from '../../../generated/http'
import { ApiError, getJob, getResult, getSelections, getSession, json, pause, request } from './client'
import { currentMetric, sessionIdentity } from './guards'

type Display = { job: Job; result: Result; value: number; session: M2Session }
export function useReference() {
  const [session, setSession] = useState<M2Session | null>(null)
  const [status, setStatus] = useState('Connecting')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [editing, setEditing] = useState(false)
  const [display, setDisplay] = useState<Display | null>(null)
  const sessionRef = useRef<M2Session | null>(null)
  const displayRef = useRef<Display | null>(null)
  const generation = useRef(0)
  const operation = useRef<AbortController | null>(null)
  const editRef = useRef(false)
  const connectedOnce = useRef(false)
  const setCurrentSession = (s: M2Session | null) => { sessionRef.current = s; setSession(s) }
  const clear = () => { displayRef.current = null; setDisplay(null) }
  const invalidate = () => { generation.current++; operation.current?.abort(); operation.current = null; clear(); setBusy(false) }
  useEffect(() => {
    const monitor = new AbortController()
    const loop = async () => {
      while (!monitor.signal.aborted) {
        const g = generation.current
        try {
          const fresh = await getSession(monitor.signal)
          if (g !== generation.current || editRef.current) { await pause(500, monitor.signal); continue }
          if (fresh.mode !== 'synthetic_one_tree_reference' || fresh.scenario.scope !== 'accepted' || fresh.layout.placements.length !== 1 || !fresh.scenario.input.proposed_layout_ref || fresh.scenario.input.proposed_layout_ref.layout_id !== fresh.layout.layout_id || fresh.scenario.input.proposed_layout_ref.revision !== fresh.layout.revision || !fresh.profile.states[fresh.scenario.input.evaluation_cases[0]?.profile_state]) throw new Error('Invalid reference session')
          connectedOnce.current = true
          const old = sessionRef.current
          if (old && sessionIdentity(old) !== sessionIdentity(fresh)) { invalidate(); setStatus('Input changed — evaluate again'); setError('The accepted reference changed. Evaluate again for a current result.') }
          if (!old || sessionIdentity(old) !== sessionIdentity(fresh)) setCurrentSession(fresh)
          const shown = displayRef.current
          if (shown) {
            const selection = await getSelections(fresh, monitor.signal)
            if (g === generation.current && displayRef.current === shown && (sessionIdentity(fresh) !== sessionIdentity(shown.session) || currentMetric(fresh, shown.job, shown.result, selection) === null)) {
              invalidate(); setStatus('Result no longer current'); setError('The current selection changed. Evaluate again.')
            }
          }
          if (!old && !displayRef.current) setStatus('Ready')
        } catch (e) {
          if (monitor.signal.aborted) break
          if (g === generation.current && !editRef.current) {
            invalidate(); setCurrentSession(null)
            if (e instanceof ApiError && e.status === 404 && !connectedOnce.current) { setStatus('Disconnected preview') }
            else { setStatus('Reference unavailable'); setError('Reference source or API is unavailable. Restore it, then evaluate again.') }
          }
        }
        try { await pause(1000, monitor.signal) } catch { break }
      }
    }
    void loop()
    return () => { monitor.abort(); operation.current?.abort(); generation.current++ }
  }, [])
  const evaluate = async () => {
    const s = sessionRef.current
    if (!s || operation.current || editRef.current || !s.scenario.input.proposed_layout_ref) return
    invalidate(); const g = generation.current; const ctl = new AbortController(); operation.current = ctl
    setBusy(true); setError(''); setStatus('Submitting')
    try {
      let job = await request<Job>('/api/v1/jobs', ctl.signal, json('POST', { request_id: crypto.randomUUID(), operation: 'evaluate_layout', scenario_ref: { scenario_id: s.scenario.scenario_id, revision: s.scenario.revision, scope: 'accepted' }, arguments: { layout_ref: s.scenario.input.proposed_layout_ref } }))
      const deadline = Date.now() + 120000
      while (job.status === 'queued' || job.status === 'running') {
        if (Date.now() >= deadline) throw new Error('Evaluation timed out')
        if (g !== generation.current) return
        setStatus(job.status === 'queued' ? 'Queued' : 'Running')
        await pause(500, ctl.signal); job = await getJob(job.job_id, ctl.signal)
      }
      if (job.status !== 'completed' || !job.run_id) throw new Error(`Evaluation ${job.status}`)
      setStatus('Checking result')
      const result = await getResult(job.run_id, ctl.signal)
      const fresh = await getSession(ctl.signal)
      const selections = await getSelections(fresh, ctl.signal)
      if (g !== generation.current) return
      const value = sessionIdentity(s) === sessionIdentity(fresh) ? currentMetric(fresh, job, result, selections) : null
      if (value === null) throw new Error('Result is not current')
      const next = { session: fresh, job, result, value }; displayRef.current = next; setDisplay(next); setStatus('Completed')
    } catch (e) {
      if (g === generation.current && !ctl.signal.aborted) { clear(); setStatus('Evaluation unavailable'); setError(e instanceof ApiError && e.status === 409 ? 'The accepted revision changed. Refreshing the reference; evaluate again.' : 'Evaluation failed, timed out, or is no longer current. Check the reference and evaluate again.') }
    } finally { if (g === generation.current) { operation.current = null; setBusy(false) } }
  }
  const place = async (position: readonly [number, number, number]) => {
    const s = sessionRef.current
    if (!s || editRef.current || s.layout.placements.length !== 1) return
    invalidate(); const g = generation.current; const ctl = new AbortController(); operation.current = ctl; editRef.current = true; setEditing(true); setError(''); setStatus('Updating input')
    try {
      const layout = { ...s.layout, layout_id: crypto.randomUUID(), revision: 1, placements: [{ ...s.layout.placements[0], position_enu_m: position }] }
      await request('/api/v1/layouts', ctl.signal, json('POST', layout))
      await request(`/api/v1/scenarios/${encodeURIComponent(s.scenario.scenario_id)}`, ctl.signal, json('PUT', { ...s.scenario.input, proposed_layout_ref: { layout_id: layout.layout_id, revision: 1 } }, { 'If-Match': `"${s.scenario.revision}"` }))
      const fresh = await getSession(ctl.signal)
      if (g !== generation.current) return
      setCurrentSession(fresh); setStatus('Input updated — ready to evaluate')
    } catch (e) {
      if (g === generation.current && !ctl.signal.aborted) { setCurrentSession(null); setStatus('Input update failed'); setError(e instanceof ApiError && e.status === 409 ? 'The accepted revision changed. Refreshing; no overwrite was attempted.' : 'The input could not be updated. Refresh the reference before trying again.') }
    } finally { if (g === generation.current) { operation.current = null; editRef.current = false; setEditing(false) } }
  }
  return { session, status, error, busy, editing, display, evaluate, place }
}
