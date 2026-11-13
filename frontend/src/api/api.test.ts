import { describe, expect, it } from 'vitest'
import { ApiError, CanopyClient, type FetchLike } from './client'
import { sha256Hex, verifyDeclaration, type DevSession } from './session'
import type { SiteBundle } from './types'
import { PROVISIONAL_ENU_TO_THREE, applyRowMajor, checkSiteTransform, enuToViewer, viewerToEnu } from '../scene/transform'

type Call = { url: string; init?: RequestInit }
function fakeFetch(handler: (call: Call) => { status: number; body: unknown }) {
  const calls: Call[] = []
  const fetcher: FetchLike = async (url, init) => {
    calls.push({ url, init })
    const { status, body } = handler({ url, init })
    return new Response(body === undefined ? '' : JSON.stringify(body), { status })
  }
  return { fetcher, calls }
}

describe('CanopyClient', () => {
  it('sends If-Match as a quoted revision when replacing a scenario', async () => {
    const { fetcher, calls } = fakeFetch(() => ({ status: 200, body: { revision: 4 } }))
    await new CanopyClient('/api/v1', fetcher).replaceScenario('s1', {} as never, 3)
    expect(calls[0].url).toBe('/api/v1/scenarios/s1')
    expect(calls[0].init?.method).toBe('PUT')
    expect((calls[0].init?.headers as Record<string, string>)['If-Match']).toBe('"3"')
  })

  it('surfaces the backend ContractError code', async () => {
    const error = { code: 'REVISION_CONFLICT', message: 'stale', retryable: false, field_errors: [], details: {} }
    const { fetcher } = fakeFetch(() => ({ status: 409, body: error }))
    const failure = await new CanopyClient('/api/v1', fetcher).scenario({ scenario_id: 's1', revision: 1 }).catch(e => e)
    expect(failure).toBeInstanceOf(ApiError)
    expect(failure.code).toBe('REVISION_CONFLICT')
  })

  it('reports an unreachable backend as NETWORK rather than a result', async () => {
    const client = new CanopyClient('/api/v1', async () => { throw new TypeError('Failed to fetch') })
    const failure = await client.health().catch(e => e)
    expect(failure.code).toBe('NETWORK')
  })

  it('finds the head revision by probing until UNKNOWN_REVISION', async () => {
    const { fetcher } = fakeFetch(({ url }) => {
      const revision = Number(new URL(url, 'http://x').searchParams.get('revision'))
      return revision <= 4
        ? { status: 200, body: { scenario_id: 's1', revision } }
        : { status: 404, body: { code: 'UNKNOWN_REVISION', message: 'nf', retryable: false, field_errors: [], details: {} } }
    })
    const head = await new CanopyClient('/api/v1', fetcher).latestScenario('s1', 2)
    expect(head.revision).toBe(4)
  })

  it('posts cancellation to the job endpoint', async () => {
    const { fetcher, calls } = fakeFetch(() => ({ status: 200, body: { job_id: 'j1', status: 'cancelled' } }))
    const job = await new CanopyClient('/api/v1', fetcher).cancelJob('j1')
    expect(calls[0].url).toBe('/api/v1/jobs/j1/cancel')
    expect(calls[0].init?.method).toBe('POST')
    expect(job.status).toBe('cancelled')
  })
})

describe('declaration verification', () => {
  // Labelled synthetic test declaration; the integrated check uses the real runtime's bytes.
  const bytes = new TextEncoder().encode(JSON.stringify({
    kind: 'synthetic', target_id: 't', receiver_point: [0, 0, 0], receiver_normal: [0, 0, 1], receiver_area_m2: 2,
    sun_direction: [0, -0.7071067811865476, 0.7071067811865476], above_horizon: true, midpoint_utc: '2026-07-01T12:00:00Z',
    duration_h: 1, obstacle_ellipsoids: [], evidence: 'test',
  }))
  const b64 = btoa(String.fromCharCode(...bytes))
  const session = { declaration_asset_id: 'a', declaration_b64: b64 } as DevSession
  const site = (sha256: string) => ({ assets: [{ asset_id: 'a', sha256 }] }) as unknown as SiteBundle

  it('draws geometry only when the bytes match the registered asset hash', async () => {
    const digest = await sha256Hex(bytes)
    const ok = await verifyDeclaration(session, site(digest))
    expect(ok.status).toBe('verified')
    const bad = await verifyDeclaration(session, site('0'.repeat(64)))
    expect(bad.status).toBe('mismatch')
    const missing = await verifyDeclaration({ ...session, declaration_asset_id: 'zzz' }, site(digest))
    expect(missing.status).toBe('missing')
  })
})

describe('viewer transform (agrees with Arnav STP-006 known points)', () => {
  it('maps ENU (1,2,3) to viewer (1,3,-2), north to -z and keeps metre scale', () => {
    expect(enuToViewer([1, 2, 3])).toEqual([1, 3, -2])
    expect(applyRowMajor(PROVISIONAL_ENU_TO_THREE, [1, 2, 3])).toEqual([1, 3, -2])
    expect(enuToViewer([0, 1, 0])).toEqual([0, 0, -1])
    expect(viewerToEnu(enuToViewer([1.5, -2.25, 0.5]))).toEqual([1.5, -2.25, 0.5])
    const [a, b] = [enuToViewer([0, 0, 0]), enuToViewer([3, 4, 0])]
    expect(Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2])).toBe(5)
  })
  it('flags an identity analysis_to_viewer rather than reinterpreting it silently', () => {
    const identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    expect(checkSiteTransform({ analysis_frame: 'enu_m', analysis_to_viewer: identity as never }).status).toBe('identity-unresolved')
    expect(checkSiteTransform({ analysis_frame: 'enu_m', analysis_to_viewer: PROVISIONAL_ENU_TO_THREE as never }).status).toBe('matches-provisional')
  })
})
