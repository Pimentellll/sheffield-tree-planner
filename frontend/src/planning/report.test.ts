import { describe, expect, it } from 'vitest'
import type { Layout, Result, Scenario, SiteBundle, TreeProfile } from '../api/types'
import { STANDING_SURVEY_REQUIREMENTS, exportGate, positionLabel, reviewPack, surveyView } from './report'

// LABELLED SYNTHETIC TEST INPUTS shaped like generated contracts, for pure report logic only.
const rights = (export_status: string) => ({ source_id: 'src-1234567890abc', export_status, local_use_status: 'permitted', team_share_status: 'permitted', public_display_status: 'permitted', required_attribution: 'A', licence_reference: 'L', source_reference: 'S', evidence: ['e'] })
const site = (over: Record<string, unknown> = {}) => ({
  site_id: 'site', name: 'Test', site_kind: 'synthetic_test', origin: { latitude_deg: 0, longitude_deg: 0, height_m: 0 }, rights: [rights('permitted')],
  readiness: { blockers: [], warnings: ['w'], optional_missing_inputs: [], survey_requirements: ['site req'] },
  coverage: { horizon_limitations: ['h'], boundary_limitations: [], missing_region_refs: ['r1'], study_extent_ref: 'x', context_extent_ref: 'y' }, ...over,
}) as unknown as SiteBundle
const scenario = { scenario_id: 's', revision: 3, input: { constraints: { survey_requirements: ['scenario req', 'site req'] } } } as unknown as Scenario
const result = { run_id: 'run' } as unknown as Result

describe('exportGate', () => {
  it('allows export only with permitted rights and a current result', () => {
    expect(exportGate(site(), result, 'current').allowed).toBe(true)
    expect(exportGate(site(), result, 'stale-draft').reasons.join()).toMatch(/not current/)
    expect(exportGate(site(), null, null).reasons.join()).toMatch(/No evaluated result/)
    const blocked = exportGate(site({ rights: [rights('unknown')] }), result, 'current')
    expect(blocked.allowed).toBe(false)
    expect(blocked.reasons.join()).toMatch(/export is unknown/)
    expect(exportGate(site({ rights: [] }), result, 'current').allowed).toBe(false)
  })
})

describe('positionLabel', () => {
  it('never shows latitude/longitude for a synthetic site', () => {
    expect(positionLabel(site(), [1, 2, 0]).kind).toBe('enu-only')
  })
  it('gives a labelled approximation for a real site with an origin', () => {
    const label = positionLabel(site({ site_kind: 'real_site', origin: { latitude_deg: 53.38, longitude_deg: -1.49, height_m: 0 } }), [0, 111.195, 0])
    expect(label.kind).toBe('approximate-wgs84')
    if (label.kind === 'approximate-wgs84') {
      expect(label.latitude).toBeCloseTo(53.381, 5)
      expect(label.longitude).toBeCloseTo(-1.49, 9)
      expect(label.reason).toMatch(/Approximate/)
    }
  })
  it('treats a (0, 0) real-site origin as unset', () => {
    expect(positionLabel(site({ site_kind: 'real_site' }), [1, 1, 0]).kind).toBe('enu-only')
  })
})

describe('surveyView and reviewPack', () => {
  it('merges recorded survey requirements and always lists standing professional checks', () => {
    const v = surveyView(site(), scenario)
    expect(v.recorded).toEqual(['scenario req', 'site req'])
    expect(v.standing).toEqual(STANDING_SURVEY_REQUIREMENTS)
    expect(v.coverageLimits).toEqual(['h', 'Missing region: r1'])
  })
  it('copies backend records unchanged', () => {
    const layout = { layout_id: 'L', placements: [{ placement_id: 'p', position_enu_m: [1, 2, 0] }] } as unknown as Layout
    const profile = { profile_id: 'pr' } as unknown as TreeProfile
    const pack = reviewPack({ site: site(), scenario, layout, profile, result, nowIso: 'T', apiVersion: '0.2.0' })
    expect(pack.result).toBe(result)
    expect(pack.scenario).toBe(scenario)
    expect(pack.status).toMatch(/SYNTHETIC/)
    expect(pack.placements[0].geographic.kind).toBe('enu-only')
    expect(pack.export_handler).toMatch(/not available/)
  })
})
