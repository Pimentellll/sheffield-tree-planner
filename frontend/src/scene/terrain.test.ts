import { describe, expect, it } from 'vitest'
import { bngToScene, buildTerrainMesh, parseTerrainMeta, surfaceAt } from './terrain'

// LABELLED SYNTHETIC TEST INPUT: a 3×2 grid, 2 m cells. DTM then DSM, rows north to south.
const meta = { cols: 3, rows: 2, spacing_m: 2, box_bng: [100, 200, 106, 204] as [number, number, number, number] }
const heights = new Float32Array([10, 10, 11, 10, 10, 12, /* dsm */ 10, 25, 11, 10, NaN, 12.2])

describe('buildTerrainMesh', () => {
  const mesh = buildTerrainMesh(meta, heights)
  it('uses stored surface heights minus one base, with no exaggeration', () => {
    expect(mesh.baseHeight).toBe(10)
    expect(mesh.positions[1 * 3 + 1]).toBe(15) // 25 − 10
    expect(mesh.positions[2 * 3 + 1]).toBe(1)
  })
  it('places row 0 at the north edge (north = −z) and columns west to east', () => {
    expect(mesh.positions[2]).toBeLessThan(mesh.positions[3 * 3 + 2])
    expect(mesh.positions[0]).toBeLessThan(mesh.positions[2 * 3])
    expect([mesh.widthM, mesh.depthM]).toEqual([4, 2])
  })
  it('counts no-data cells and still builds every triangle', () => {
    expect(mesh.gapCells).toBe(1)
    expect(mesh.indices.length).toBe(2 * 1 * 6)
  })
  it('colours by height above ground bands', () => {
    const colourOf = (i: number) => Array.from(mesh.colors.slice(i * 3, i * 3 + 3))
    expect(colourOf(1)).not.toEqual(colourOf(0)) // 15 m above ground vs ground
  })
  it('rejects a payload of the wrong size', () => {
    expect(() => buildTerrainMesh(meta, new Float32Array(5))).toThrow()
  })
})

describe('coordinates', () => {
  it('maps BNG to scene with north towards −z', () => {
    const [x0, z0] = bngToScene(meta, 101, 203) // centre of the north-west cell
    expect([x0, z0]).toEqual([-2, -1])
    const [, zSouth] = bngToScene(meta, 101, 201)
    expect(zSouth).toBeGreaterThan(z0)
  })
  it('samples the stored surface at a BNG point', () => {
    expect(surfaceAt(meta, heights, 10, 103, 203)).toBe(15)
    expect(surfaceAt(meta, heights, 10, 103, 201)).toBeNull() // NaN cell
    expect(surfaceAt(meta, heights, 10, 999, 203)).toBeNull()
  })
})

describe('parseTerrainMeta', () => {
  const good = { kind: 'canopy-terrain-context/1', cols: 3, rows: 2, spacing_m: 2, box_bng: [0, 0, 6, 4], bin: 'a.bin', bin_sha256: 'a'.repeat(64), attribution: 'x', licence: 'y', synthetic_test: false }
  it('accepts the documented shape and rejects unsafe file names or sizes', () => {
    expect(parseTerrainMeta(good)).not.toBeNull()
    expect(parseTerrainMeta({ ...good, bin: '../secret.bin' })).toBeNull()
    expect(parseTerrainMeta({ ...good, cols: 100000 })).toBeNull()
    expect(parseTerrainMeta({ ...good, kind: 'other' })).toBeNull()
  })
})
