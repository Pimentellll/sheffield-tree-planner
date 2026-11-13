import type { ScenarioRef, SiteBundle, Vec3 } from './types'

/**
 * Explicit synthetic numerical inputs declared by the reference runtime (evaluators/runtime.py,
 * SyntheticScene.declaration). The SiteBundle only references these by asset id, so the viewer
 * receives the exact registered asset bytes and checks them against the SiteBundle SHA-256.
 */
export interface SyntheticDeclaration {
  readonly kind: string
  readonly target_id: string
  readonly receiver_point: Vec3
  readonly receiver_normal: Vec3
  readonly receiver_area_m2: number
  readonly sun_direction: Vec3
  readonly above_horizon: boolean
  readonly midpoint_utc: string
  readonly duration_h: number
  readonly obstacle_ellipsoids: ReadonlyArray<readonly [Vec3, Vec3]>
  readonly evidence: string
}

/** Ben's takeover-v1 physical scene (`canopy-physical-scene/1`), drawn as declared. */
export interface PhysicalScene {
  readonly format_version: 'canopy-physical-scene/1'
  readonly spatial_spacing_m: number
  readonly flat_ground_z_m: number
  readonly samples: ReadonlyArray<{ readonly sample_id: string; readonly position_enu_m: Vec3; readonly normal_enu: Vec3; readonly area_m2: number; readonly target_id: string }>
  readonly triangles: ReadonlyArray<{ readonly triangle_id: string; readonly vertices_enu_m: readonly [Vec3, Vec3, Vec3] }>
  readonly existing_trees: readonly unknown[]
  readonly regions: Readonly<Record<string, ReadonlyArray<readonly [number, number]>>>
}

export type SceneData =
  | { readonly kind: 'reference'; readonly declaration: SyntheticDeclaration }
  | { readonly kind: 'physical'; readonly scene: PhysicalScene }

export interface DevSession {
  readonly kind: 'canopy-dev-session'
  readonly label: string
  readonly scenario_ref: ScenarioRef
  readonly declaration_asset_id: string
  readonly declaration_b64: string
  readonly numerical_source_commit: string
  readonly started_at_utc: string
}

export type DeclarationCheck =
  | { readonly status: 'verified'; readonly scene: SceneData; readonly sha256: string }
  | { readonly status: 'mismatch' | 'missing' | 'invalid'; readonly reason: string }

export function decodeBase64(value: string): Uint8Array {
  const binary = atob(value)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
  return bytes
}

export async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', bytes as BufferSource)
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('')
}

const isVec3 = (value: unknown): value is Vec3 =>
  Array.isArray(value) && value.length === 3 && value.every(x => typeof x === 'number' && Number.isFinite(x))

function parsePhysical(value: unknown): PhysicalScene | null {
  const p = value as PhysicalScene
  if (typeof p !== 'object' || p === null || p.format_version !== 'canopy-physical-scene/1') return null
  if (!Array.isArray(p.samples) || !p.samples.every(x => isVec3(x?.position_enu_m) && typeof x.area_m2 === 'number' && x.area_m2 > 0)) return null
  if (!Array.isArray(p.triangles) || !p.triangles.every(t => Array.isArray(t?.vertices_enu_m) && t.vertices_enu_m.length === 3 && t.vertices_enu_m.every(isVec3))) return null
  const regions = p.regions ?? {}
  if (typeof regions !== 'object' || !Object.values(regions).every(r => Array.isArray(r) && r.every(pt => Array.isArray(pt) && pt.length >= 2 && pt.every(n => typeof n === 'number')))) return null
  if (typeof p.flat_ground_z_m !== 'number' || !Array.isArray(p.existing_trees)) return null
  return { ...p, regions }
}

function parseScene(bytes: Uint8Array): SceneData | null {
  let value: unknown
  try {
    value = JSON.parse(new TextDecoder().decode(bytes))
  } catch {
    return null
  }
  const physical = parsePhysical(value)
  if (physical) return { kind: 'physical', scene: physical }
  const declaration = parseDeclaration(value)
  return declaration ? { kind: 'reference', declaration } : null
}

function parseDeclaration(value: unknown): SyntheticDeclaration | null {
  const d = value as SyntheticDeclaration
  if (
    typeof d !== 'object' || d === null || !isVec3(d.receiver_point) || !isVec3(d.receiver_normal) ||
    !isVec3(d.sun_direction) || typeof d.receiver_area_m2 !== 'number' || !(d.receiver_area_m2 > 0) ||
    typeof d.target_id !== 'string' || !Array.isArray(d.obstacle_ellipsoids) ||
    !d.obstacle_ellipsoids.every(o => Array.isArray(o) && o.length === 2 && isVec3(o[0]) && isVec3(o[1]))
  ) return null
  return d
}

/** Only geometry whose bytes hash to the SiteBundle's registered asset is drawn. */
export async function verifyDeclaration(session: DevSession, site: SiteBundle): Promise<DeclarationCheck> {
  const asset = site.assets.find(item => item.asset_id === session.declaration_asset_id)
  if (!asset) return { status: 'missing', reason: `SiteBundle has no asset ${session.declaration_asset_id}` }
  let bytes: Uint8Array
  try {
    bytes = decodeBase64(session.declaration_b64)
  } catch {
    return { status: 'invalid', reason: 'Declaration bytes are not valid base64' }
  }
  const digest = await sha256Hex(bytes)
  if (digest !== asset.sha256) return { status: 'mismatch', reason: `Declaration SHA-256 ${digest.slice(0, 12)}… differs from registered ${asset.sha256.slice(0, 12)}…` }
  const scene = parseScene(bytes)
  if (!scene) return { status: 'invalid', reason: 'Scene bytes are not a recognised scene format' }
  return { status: 'verified', scene, sha256: digest }
}

/** The dev launcher serves its session at this path through the Vite dev server. */
export async function loadDevSession(fetcher: typeof fetch = fetch): Promise<DevSession | null> {
  try {
    const response = await fetcher('/canopy-dev-session.json', { cache: 'no-store' })
    if (!response.ok) return null
    const value = (await response.json()) as DevSession
    return value?.kind === 'canopy-dev-session' ? value : null
  } catch {
    return null
  }
}
