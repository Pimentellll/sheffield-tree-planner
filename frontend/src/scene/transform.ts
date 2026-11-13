import type { SiteBundle, Vec3 } from '../api/types'

/**
 * Provisional ENU (east, north, up) metres -> Three.js (x, y, z) = (east, up, -north).
 * Row-major 4x4 for column vectors. Matches Arnav's STP-006 draft ANALYSIS_TO_VIEWER_DRAFT
 * known-point checks: ENU (1,2,3) -> (1,3,-2); true north (0,1,0) -> (0,0,-1); 1 m stays 1 m.
 */
export const PROVISIONAL_ENU_TO_THREE: readonly (readonly number[])[] = [
  [1, 0, 0, 0],
  [0, 0, 1, 0],
  [0, -1, 0, 0],
  [0, 0, 0, 1],
]

export const enuToViewer = ([e, n, u]: readonly number[]): Vec3 => [e, u, -n + 0] as unknown as Vec3
export const viewerToEnu = ([x, y, z]: readonly number[]): Vec3 => [x, -z + 0, y] as unknown as Vec3

const IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
const same = (a: readonly (readonly number[])[], b: readonly (readonly number[])[]) =>
  a.length === 4 && a.every((row, i) => row.length === 4 && row.every((x, j) => Math.abs(x - b[i][j]) < 1e-12))

export type TransformCheck =
  | { readonly status: 'matches-provisional'; readonly detail: string }
  | { readonly status: 'identity-unresolved'; readonly detail: string }
  | { readonly status: 'unsupported'; readonly detail: string }

/**
 * The viewer only draws with the documented provisional transform. It reports, rather than
 * silently reinterprets, a SiteBundle matrix that disagrees with it.
 */
export function checkSiteTransform(site: Pick<SiteBundle, 'analysis_to_viewer' | 'analysis_frame'>): TransformCheck {
  if (site.analysis_frame !== 'enu_m') return { status: 'unsupported', detail: `Unknown analysis frame ${String(site.analysis_frame)}` }
  if (same(site.analysis_to_viewer, PROVISIONAL_ENU_TO_THREE)) {
    return { status: 'matches-provisional', detail: 'SiteBundle analysis_to_viewer equals the provisional ENU → (east, up, −north) transform.' }
  }
  if (same(site.analysis_to_viewer, IDENTITY)) {
    return {
      status: 'identity-unresolved',
      detail: 'SiteBundle analysis_to_viewer is identity, which in a y-up viewer would put north towards the sky. Drawn with the provisional ENU → (east, up, −north) transform instead; contract clarification requested.',
    }
  }
  return { status: 'unsupported', detail: 'SiteBundle analysis_to_viewer is neither identity nor the provisional transform; geometry is drawn with the provisional transform and must not be trusted for orientation.' }
}

export function applyRowMajor(m: readonly (readonly number[])[], p: readonly number[]): Vec3 {
  const v = [p[0], p[1], p[2], 1]
  const out = [0, 1, 2].map(i => m[i].reduce((sum, x, j) => sum + x * v[j], 0) + 0)
  return out as unknown as Vec3
}
