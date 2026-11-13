/** View-only terrain context (`canopy-terrain-context/1`), written by scripts/prepare_terrain.py. */
export interface TerrainMeta {
  readonly kind: 'canopy-terrain-context/1'
  readonly name: string
  readonly title: string
  readonly synthetic_test: boolean
  readonly crs: string
  readonly box_bng: readonly [number, number, number, number]
  readonly spacing_m: number
  readonly cols: number
  readonly rows: number
  readonly bin: string
  readonly bin_sha256: string
  readonly reduction: string
  readonly vertical_datum: string
  readonly survey: string
  readonly licence: string
  readonly attribution: string
  readonly sources: ReadonlyArray<{ readonly role: string; readonly file: string; readonly download_sha256: string }>
  readonly stats: { readonly dtm_min_m: number; readonly dtm_max_m: number; readonly max_height_above_ground_m: number; readonly nodata_cells: number }
  readonly boxes: ReadonlyArray<{ readonly label: string; readonly bng: readonly [number, number, number, number] }>
  readonly markers: ReadonlyArray<{ readonly label: string; readonly bng: readonly [number, number]; readonly note?: string }>
  readonly limitations: readonly string[]
}

export function parseTerrainMeta(value: unknown): TerrainMeta | null {
  const m = value as TerrainMeta
  const int = (n: unknown) => Number.isInteger(n) && (n as number) > 1 && (n as number) <= 4096
  if (typeof m !== 'object' || m === null || m.kind !== 'canopy-terrain-context/1') return null
  if (!int(m.cols) || !int(m.rows) || !(m.spacing_m > 0) || !Array.isArray(m.box_bng) || m.box_bng.length !== 4) return null
  if (typeof m.bin !== 'string' || !/^[\w.-]+\.bin$/.test(m.bin) || !/^[0-9a-f]{64}$/.test(m.bin_sha256)) return null
  if (typeof m.attribution !== 'string' || typeof m.licence !== 'string' || typeof m.synthetic_test !== 'boolean') return null
  return { ...m, boxes: m.boxes ?? [], markers: m.markers ?? [], limitations: m.limitations ?? [], sources: m.sources ?? [] }
}

export interface TerrainMesh {
  readonly positions: Float32Array
  readonly colors: Float32Array
  readonly indices: Uint32Array
  /** Ground height subtracted from every vertex so the scene sits near y = 0. */
  readonly baseHeight: number
  readonly widthM: number
  readonly depthM: number
  readonly gapCells: number
}

/** Height above ground (DSM − DTM) bands. Elevated cells are NOT classified as building or canopy. */
export const HEIGHT_BANDS = [
  { upTo: 0.5, label: 'Ground (under 0.5 m above terrain)', rgb: [0.42, 0.56, 0.38] },
  { upTo: 2.5, label: 'Low surface, 0.5–2.5 m', rgb: [0.55, 0.66, 0.4] },
  { upTo: 12, label: 'Elevated 2.5–12 m (building or canopy, unclassified)', rgb: [0.79, 0.74, 0.6] },
  { upTo: Infinity, label: 'Elevated over 12 m', rgb: [0.93, 0.9, 0.84] },
] as const

const GAP_RGB = [0.16, 0.2, 0.18]

/**
 * Build a surface mesh from the stored heights. x = easting, y = up, z = −northing, centred on the box.
 * Heights are used exactly as stored (minus one constant base); no smoothing or vertical exaggeration.
 */
export function buildTerrainMesh(meta: Pick<TerrainMeta, 'cols' | 'rows' | 'spacing_m'>, heights: Float32Array): TerrainMesh {
  const { cols, rows, spacing_m: s } = meta
  const n = cols * rows
  if (heights.length !== n * 2) throw new Error(`Terrain payload has ${heights.length} values, expected ${n * 2}`)
  let base = Infinity
  for (let i = 0; i < n; i += 1) if (Number.isFinite(heights[i]) && heights[i] < base) base = heights[i]
  if (!Number.isFinite(base)) throw new Error('Terrain has no valid ground heights')
  const positions = new Float32Array(n * 3)
  const colors = new Float32Array(n * 3)
  const widthM = (cols - 1) * s
  const depthM = (rows - 1) * s
  let gapCells = 0
  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      const i = r * cols + c
      const ground = heights[i]
      const surface = heights[n + i]
      const valid = Number.isFinite(ground) && Number.isFinite(surface)
      if (!valid) gapCells += 1
      const above = valid ? Math.max(0, surface - ground) : 0
      positions[i * 3] = c * s - widthM / 2
      positions[i * 3 + 1] = valid ? surface - base : (Number.isFinite(ground) ? ground - base : 0)
      positions[i * 3 + 2] = r * s - depthM / 2 // row 0 is the north edge, so north = −z
      const band = valid ? HEIGHT_BANDS.find(b => above < b.upTo)!.rgb : GAP_RGB
      // Slight darkening with relative ground height keeps slopes readable; it is shading, not data.
      const shade = valid && above < 0.5 ? 0.85 + 0.15 * Math.min(1, (ground - base) / 40) : 1
      colors[i * 3] = band[0] * shade
      colors[i * 3 + 1] = band[1] * shade
      colors[i * 3 + 2] = band[2] * shade
    }
  }
  const indices = new Uint32Array((cols - 1) * (rows - 1) * 6)
  let k = 0
  for (let r = 0; r < rows - 1; r += 1) {
    for (let c = 0; c < cols - 1; c += 1) {
      const a = r * cols + c
      indices[k++] = a; indices[k++] = a + cols; indices[k++] = a + 1
      indices[k++] = a + 1; indices[k++] = a + cols; indices[k++] = a + cols + 1
    }
  }
  return { positions, colors, indices, baseHeight: base, widthM, depthM, gapCells }
}

/** BNG easting/northing to scene x/z for a terrain box. */
export function bngToScene(meta: Pick<TerrainMeta, 'box_bng' | 'cols' | 'rows' | 'spacing_m'>, easting: number, northing: number): [number, number] {
  const widthM = (meta.cols - 1) * meta.spacing_m
  const depthM = (meta.rows - 1) * meta.spacing_m
  // Cell centres: the first column is half a cell in from the west edge, the first row half a cell below the north edge.
  const x = easting - (meta.box_bng[0] + meta.spacing_m / 2) - widthM / 2
  const z = (meta.box_bng[3] - meta.spacing_m / 2) - northing - depthM / 2
  return [x, z]
}

/** Stored surface height (relative to the mesh base) at the cell nearest a BNG point, or null outside/no data. */
export function surfaceAt(meta: Pick<TerrainMeta, 'box_bng' | 'cols' | 'rows' | 'spacing_m'>, heights: Float32Array, base: number, easting: number, northing: number): number | null {
  const c = Math.floor((easting - meta.box_bng[0]) / meta.spacing_m)
  const r = Math.floor((meta.box_bng[3] - northing) / meta.spacing_m)
  if (c < 0 || r < 0 || c >= meta.cols || r >= meta.rows) return null
  const v = heights[meta.cols * meta.rows + r * meta.cols + c]
  return Number.isFinite(v) ? v - base : null
}
