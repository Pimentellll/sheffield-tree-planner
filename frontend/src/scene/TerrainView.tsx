import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { sha256Hex } from '../api/session'
import { HEIGHT_BANDS, bngToScene, buildTerrainMesh, parseTerrainMeta, surfaceAt, type TerrainMeta } from './terrain'

type Load =
  | { readonly status: 'loading' }
  | { readonly status: 'absent' }
  | { readonly status: 'error'; readonly reason: string }
  | { readonly status: 'ready'; readonly meta: TerrainMeta; readonly heights: Float32Array }

const hex = (rgb: readonly number[]) => `rgb(${rgb.map(v => Math.round(v * 255)).join(' ')})`

/** View-only 3D context from real height data. Nothing here feeds or reflects the evaluator. */
export default function TerrainView({ name }: { name: string }) {
  const mountRef = useRef<HTMLDivElement>(null)
  const northRef = useRef<HTMLSpanElement>(null)
  const controlsRef = useRef<{ controls: OrbitControls; camera: THREE.PerspectiveCamera; home: THREE.Vector3 } | null>(null)
  const [load, setLoad] = useState<Load>({ status: 'loading' })
  const [webgl, setWebgl] = useState(true)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const response = await fetch(`/canopy-terrain/${name}.json`, { cache: 'no-store' })
        if (response.status === 404) { if (!cancelled) setLoad({ status: 'absent' }); return }
        const meta = parseTerrainMeta(await response.json())
        if (!meta) throw new Error('Terrain metadata is not a recognised canopy-terrain-context/1 file')
        const bytes = new Uint8Array(await (await fetch(`/canopy-terrain/${meta.bin}`, { cache: 'no-store' })).arrayBuffer())
        const digest = await sha256Hex(bytes)
        if (digest !== meta.bin_sha256) throw new Error(`Height data hash ${digest.slice(0, 12)}… does not match the metadata; not drawn`)
        if (bytes.byteLength !== meta.cols * meta.rows * 8) throw new Error('Height data size does not match the grid')
        const heights = new Float32Array(bytes.buffer, bytes.byteOffset, meta.cols * meta.rows * 2)
        if (!cancelled) setLoad({ status: 'ready', meta, heights })
      } catch (err) {
        if (!cancelled) setLoad({ status: 'error', reason: err instanceof Error ? err.message : String(err) })
      }
    })()
    return () => { cancelled = true }
  }, [name])

  useEffect(() => {
    const mount = mountRef.current
    if (!mount || load.status !== 'ready') return
    const { meta, heights } = load
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true })
    } catch {
      setWebgl(false)
      return
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setClearColor('#142820')
    renderer.domElement.setAttribute('aria-hidden', 'true')
    mount.appendChild(renderer.domElement)

    const mesh = buildTerrainMesh(meta, heights)
    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(mesh.positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(mesh.colors, 3))
    geometry.setIndex(new THREE.BufferAttribute(mesh.indices, 1))
    geometry.computeVertexNormals()
    const scene = new THREE.Scene()
    scene.add(new THREE.Mesh(geometry, new THREE.MeshLambertMaterial({ vertexColors: true })))
    scene.add(new THREE.HemisphereLight('#e8f0ea', '#4a5f50', 1.9))
    const sun = new THREE.DirectionalLight('#fff4d7', 1.7)
    sun.position.set(-0.6, 1, 0.5) // display lighting only; not a solar position
    scene.add(sun)

    const top = meta.stats.max_height_above_ground_m + (meta.stats.dtm_max_m - mesh.baseHeight)
    for (const box of meta.boxes) {
      const [x0, z0] = bngToScene(meta, box.bng[0], box.bng[3])
      const [x1, z1] = bngToScene(meta, box.bng[2], box.bng[1])
      const y = (meta.stats.dtm_max_m - mesh.baseHeight) + 3
      const pts = [[x0, z0], [x1, z0], [x1, z1], [x0, z1]].map(([x, z]) => new THREE.Vector3(x, y, z))
      const line = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineDashedMaterial({ color: '#b7e879', dashSize: 8, gapSize: 5 }))
      line.computeLineDistances()
      scene.add(line)
    }
    for (const marker of meta.markers) {
      const [x, z] = bngToScene(meta, marker.bng[0], marker.bng[1])
      const surface = surfaceAt(meta, heights, mesh.baseHeight, marker.bng[0], marker.bng[1]) ?? 0
      const pole = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x, surface, z), new THREE.Vector3(x, top + 40, z)]),
        new THREE.LineBasicMaterial({ color: '#f1d27a' }),
      )
      const head = new THREE.Mesh(new THREE.SphereGeometry(6, 16, 12), new THREE.MeshBasicMaterial({ color: '#f1d27a' }))
      head.position.set(x, top + 40, z)
      scene.add(pole, head)
    }

    const span = Math.max(mesh.widthM, mesh.depthM)
    const camera = new THREE.PerspectiveCamera(42, 1, 1, span * 8)
    const home = new THREE.Vector3(span * 0.55, span * 0.5, span * 0.75)
    camera.position.copy(home)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.target.set(0, (meta.stats.dtm_max_m - mesh.baseHeight) / 2, 0)
    controls.minDistance = 30
    controls.maxDistance = span * 3
    controls.maxPolarAngle = Math.PI / 2.05
    controlsRef.current = { controls, camera, home }
    const updateNorth = () => {
      const a = controls.target.clone().project(camera)
      const b = controls.target.clone().add(new THREE.Vector3(0, 0, -span / 4)).project(camera)
      if (northRef.current) northRef.current.style.transform = `rotate(${Math.atan2(b.x - a.x, b.y - a.y) * 180 / Math.PI}deg)`
    }
    controls.addEventListener('change', updateNorth)
    const observer = new ResizeObserver(() => {
      if (!mount.clientWidth || !mount.clientHeight) return
      renderer.setSize(mount.clientWidth, mount.clientHeight)
      camera.aspect = mount.clientWidth / mount.clientHeight
      camera.updateProjectionMatrix()
      updateNorth()
    })
    observer.observe(mount)
    let frame = 0
    const tick = () => { frame = requestAnimationFrame(tick); controls.update(); renderer.render(scene, camera) }
    tick()
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controls.dispose()
      scene.traverse(o => { if (o instanceof THREE.Mesh || o instanceof THREE.Line) { o.geometry.dispose(); (o.material as THREE.Material).dispose() } })
      renderer.dispose()
      mount.removeChild(renderer.domElement)
      controlsRef.current = null
    }
  }, [load])

  const move = (action: 'left' | 'right' | 'in' | 'out' | 'top' | 'reset') => {
    const c = controlsRef.current
    if (!c) return
    const offset = c.camera.position.clone().sub(c.controls.target)
    if (action === 'reset') { c.camera.position.copy(c.home); c.controls.target.setX(0).setZ(0) }
    else if (action === 'top') c.camera.position.copy(c.controls.target).add(new THREE.Vector3(0.001, offset.length(), 0.001))
    else if (action === 'in' || action === 'out') c.camera.position.copy(c.controls.target).add(offset.multiplyScalar(action === 'in' ? 0.75 : 1.33).clampLength(c.controls.minDistance, c.controls.maxDistance))
    else c.camera.position.copy(c.controls.target).add(offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), action === 'left' ? -Math.PI / 8 : Math.PI / 8))
    c.controls.update()
  }

  if (load.status === 'absent') {
    return (
      <section className="site-panel terrain-panel" aria-label="Terrain context" data-testid="terrain-absent">
        <div className="panel-head"><div><span className="section-kicker">REAL TERRAIN CONTEXT</span><h2>Not loaded</h2></div><span className="tiny-tag">NO DATA</span></div>
        <div className="detail-section terrain-empty"><p>No terrain file is available, so nothing is drawn. Download EA LiDAR tile SK38NW (DTM and first-return DSM), run <code>frontend/scripts/prepare_terrain.py</code>, and start the dev server with <code>CANOPY_TERRAIN_DIR</code> pointing at its output folder.</p></div>
      </section>
    )
  }
  if (load.status === 'loading' || load.status === 'error') {
    return (
      <section className="site-panel terrain-panel" aria-label="Terrain context">
        <div className="panel-head"><div><span className="section-kicker">REAL TERRAIN CONTEXT</span><h2>{load.status === 'loading' ? 'Loading…' : 'Not drawn'}</h2></div></div>
        {load.status === 'error' && <div className="detail-section terrain-empty"><p role="alert" data-testid="terrain-error">{load.reason}</p></div>}
      </section>
    )
  }
  const { meta } = load
  const km = (v: number) => `${(v / 1000).toFixed(2)} km`
  return (
    <section className="site-panel terrain-panel" aria-labelledby="terrain-heading" data-testid="terrain-view">
      <div className="panel-head">
        <div><span className="section-kicker">{meta.synthetic_test ? 'SYNTHETIC TEST TERRAIN' : 'REAL TERRAIN CONTEXT'}</span><h2 id="terrain-heading">{meta.title}</h2></div>
        <span className="tiny-tag" data-testid="terrain-tag">{meta.synthetic_test ? 'SYNTHETIC · NOT SHEFFIELD' : 'VIEW ONLY · NOT ANALYSED'}</span>
      </div>
      <div className="scene-wrap terrain-wrap" role="group" aria-label="3D terrain view. Use the camera buttons to orbit, zoom, look from above or reset.">
        <div className="scene-canvas" ref={mountRef} />
        <div className="scene-topline"><span className="pill pill-lime">{meta.synthetic_test ? 'SYNTHETIC TEST TERRAIN' : 'EA LIDAR · VIEW ONLY'}</span><span className="scene-scale">{km((meta.cols - 1) * meta.spacing_m)} × {km((meta.rows - 1) * meta.spacing_m)} · {meta.spacing_m} m cells · no vertical exaggeration</span></div>
        {!webgl && <div className="scene-message" role="alert">3D view unavailable on this device.</div>}
        <div className="north-indicator" aria-label="Grid north in the current camera view"><span ref={northRef}>↑</span> N</div>
        <div className="scene-toolbar" aria-label="Camera controls">
          <button type="button" onClick={() => move('left')} aria-label="Orbit camera left">↶</button>
          <button type="button" onClick={() => move('right')} aria-label="Orbit camera right">↷</button>
          <button type="button" onClick={() => move('in')} aria-label="Zoom in">+</button>
          <button type="button" onClick={() => move('out')} aria-label="Zoom out">−</button>
          <button type="button" onClick={() => move('top')}>From above</button>
          <button type="button" onClick={() => move('reset')}>Reset view</button>
        </div>
      </div>
      <div className="map-legend terrain-legend">
        {HEIGHT_BANDS.map(b => <span key={b.label}><i className="legend-dot" style={{ background: hex(b.rgb), borderRadius: 2, transform: 'none' }} /> {b.label}</span>)}
        {meta.boxes.map(b => <span key={b.label}><i className="legend-line region" /> {b.label}</span>)}
        {meta.markers.map(m => <span key={m.label}><i className="legend-dot" style={{ background: '#f1d27a', borderRadius: '50%', transform: 'none' }} /> {m.label}</span>)}
        <span>Drag to orbit · right-drag to pan · scroll to zoom</span>
      </div>
      <div className="detail-section terrain-notes">
        <p><strong>{meta.synthetic_test ? 'Synthetic test terrain, generated for checks. Not Sheffield.' : 'Context view only.'}</strong> This surface is not loaded into the planner and no shade result refers to it. {meta.survey}.</p>
        <ul>{meta.limitations.map(l => <li key={l}>{l}</li>)}</ul>
        <p className="fine-print">{meta.attribution} {meta.licence}. {meta.reduction}. Heights: {meta.vertical_datum}. Ground {meta.stats.dtm_min_m.toFixed(1)}–{meta.stats.dtm_max_m.toFixed(1)} m; tallest surface {meta.stats.max_height_above_ground_m.toFixed(1)} m above ground; {meta.stats.nodata_cells} no-data cells. {meta.crs}. Data sha256 {meta.bin_sha256.slice(0, 12)}…{meta.sources.map(s => ` · ${s.role.split(' ')[0]} download sha256 ${s.download_sha256.slice(0, 12)}…`).join('')}</p>
      </div>
    </section>
  )
}
