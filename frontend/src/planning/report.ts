import type { Layout, Result, Scenario, SiteBundle, TreeProfile } from '../api/types'
import type { Currentness } from './evaluation'

/** Professional checks that always remain outside this tool, whatever the data records. */
export const STANDING_SURVEY_REQUIREMENTS = [
  'Planting permission from the land manager (and heritage/conservation consent where designated)',
  'Underground services and utilities survey before any excavation',
  'Soil, rooting volume and drainage assessment',
  'Arboricultural review of species, establishment and aftercare',
] as const

export interface SurveyView {
  /** Requirements recorded in the accepted scenario and SiteBundle. */
  readonly recorded: readonly string[]
  readonly blockers: readonly string[]
  readonly warnings: readonly string[]
  readonly coverageLimits: readonly string[]
  readonly standing: readonly string[]
}

export function surveyView(site: SiteBundle, scenario: Scenario): SurveyView {
  const recorded = [...new Set([...scenario.input.constraints.survey_requirements, ...site.readiness.survey_requirements])]
  return {
    recorded,
    blockers: site.readiness.blockers,
    warnings: site.readiness.warnings,
    coverageLimits: [...site.coverage.horizon_limitations, ...site.coverage.boundary_limitations, ...site.coverage.missing_region_refs.map(r => `Missing region: ${r}`)],
    standing: STANDING_SURVEY_REQUIREMENTS,
  }
}

export type PositionLabel =
  | { readonly kind: 'enu-only'; readonly reason: string }
  | { readonly kind: 'approximate-wgs84'; readonly latitude: number; readonly longitude: number; readonly reason: string }

const R = 6_371_008.8 // mean Earth radius, metres

/**
 * Positions are ENU metres. A geographic position is offered only for a real site with a
 * non-placeholder origin, and then only as a labelled local-tangent-plane approximation.
 */
export function positionLabel(site: Pick<SiteBundle, 'site_kind' | 'origin'>, enu: readonly number[]): PositionLabel {
  const { latitude_deg: lat0, longitude_deg: lon0 } = site.origin
  if (site.site_kind !== 'real_site') return { kind: 'enu-only', reason: 'Synthetic test site: its geographic origin is a placeholder, so no latitude/longitude is shown.' }
  if (lat0 === 0 && lon0 === 0) return { kind: 'enu-only', reason: 'The SiteBundle origin is (0, 0), treated as unset.' }
  const latitude = lat0 + (enu[1] / R) * (180 / Math.PI)
  const longitude = lon0 + (enu[0] / (R * Math.cos(lat0 * Math.PI / 180))) * (180 / Math.PI)
  return { kind: 'approximate-wgs84', latitude, longitude, reason: 'Approximate WGS84 from the SiteBundle origin using a local tangent plane; for orientation, not surveying.' }
}

export interface ExportGate {
  readonly allowed: boolean
  readonly reasons: readonly string[]
}

/** Export only when every source permits export and the result shown is current. */
export function exportGate(site: SiteBundle | null, result: Result | null, currentness: Currentness | null): ExportGate {
  const reasons: string[] = []
  if (!site) reasons.push('No site loaded.')
  else {
    if (site.rights.length === 0) reasons.push('The SiteBundle records no source rights.')
    for (const r of site.rights) {
      if (r.export_status !== 'permitted') reasons.push(`Source ${r.source_id.slice(0, 12)}… export is ${r.export_status}.`)
    }
  }
  if (!result) reasons.push('No evaluated result to export.')
  else if (currentness !== 'current') reasons.push('The latest result is not current for the accepted revision (re-evaluate first).')
  return { allowed: reasons.length === 0, reasons }
}

/**
 * The review pack copies backend records verbatim. Nothing in it is computed by the client
 * except the generation timestamp and the labelled position approximation (if any).
 */
export function reviewPack(args: {
  site: SiteBundle; scenario: Scenario; layout: Layout; profile: TreeProfile; result: Result; nowIso: string; apiVersion: string
}) {
  const { site, scenario, layout, profile, result, nowIso, apiVersion } = args
  return {
    kind: 'canopy-review-pack',
    pack_version: 1,
    generated_at_utc: nowIso,
    generator: 'CANOPY frontend: client-assembled from stored backend records',
    export_handler: 'none: the backend prepare_proposal operation is not available; records below are copied unchanged',
    backend_version: apiVersion,
    status: site.site_kind === 'synthetic_test' ? 'SYNTHETIC TEST SITE: not Sheffield; not a planting proposal' : 'Proposal for review: not planting permission',
    positions_frame: 'analysis ENU metres (east, north, up) from the SiteBundle origin',
    placements: layout.placements.map(p => ({ placement_id: p.placement_id, position_enu_m: p.position_enu_m, geographic: positionLabel(site, p.position_enu_m) })),
    attributions: site.rights.map(r => ({ source_id: r.source_id, required_attribution: r.required_attribution, licence_reference: r.licence_reference })),
    survey: surveyView(site, scenario),
    site: {
      site_id: site.site_id, name: site.name, site_kind: site.site_kind, scene_revision: site.scene_revision, semantic_revision: site.semantic_revision,
      geometry_fingerprint: site.geometry_fingerprint, analysis_frame: site.analysis_frame, horizontal_crs: site.horizontal_crs, origin: site.origin,
      vertical_datum: site.vertical_datum, rights: site.rights, coverage: site.coverage, readiness: site.readiness,
    },
    scenario,
    layout,
    profile,
    result,
  }
}
