import type { M2Session } from '../../../generated/contracts'
import type { Job, Result, ScenarioSelections } from '../../../generated/http'

export class ApiError extends Error { constructor(public status: number) { super(`Reference API request failed (${status})`) } }
export async function request<T>(url: string, signal: AbortSignal, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, signal, cache: 'no-store' })
  if (!response.ok) throw new ApiError(response.status)
  return await response.json() as T
}
export const getSession = (signal: AbortSignal) => request<M2Session>('/m2/session', signal)
export const getJob = (id: string, signal: AbortSignal) => request<Job>(`/api/v1/jobs/${encodeURIComponent(id)}`, signal)
export const getResult = (id: string, signal: AbortSignal) => request<Result>(`/api/v1/results/${encodeURIComponent(id)}`, signal)
export const getSelections = (s: M2Session, signal: AbortSignal) => request<ScenarioSelections>(`/api/v1/scenarios/${encodeURIComponent(s.scenario.scenario_id)}/selections?revision=${s.scenario.revision}&scope=accepted`, signal)
export const json = (method: string, body: unknown, headers?: Record<string, string>): RequestInit => ({ method, headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body) })
export const pause = (ms: number, signal: AbortSignal) => new Promise<void>((resolve, reject) => {
  if (signal.aborted) { reject(new DOMException('Aborted', 'AbortError')); return }
  const timer = setTimeout(() => { signal.removeEventListener('abort', abort); resolve() }, ms)
  const abort = () => { clearTimeout(timer); reject(new DOMException('Aborted', 'AbortError')) }
  signal.addEventListener('abort', abort, { once: true })
})
