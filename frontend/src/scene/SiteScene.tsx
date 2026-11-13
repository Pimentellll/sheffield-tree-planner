import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import type { SceneData } from '../api/session'
import type { TreeState, Vec3 } from '../api/types'
import { clampPosition, nudge } from '../planning/evaluation'
import { enuToViewer, viewerToEnu } from './transform'

type SceneState = 'loading' | 'ready' | 'error'
type CameraAction = 'left' | 'right' | 'zoomIn' | 'zoomOut' | 'reset' | 'tree'

export interface CandidateMarker { readonly id: string; readonly position: Vec3; readonly selected: boolean }

export interface SiteSceneProps {
  readonly scene: SceneData | null
  /** Catalogue positions; when present, editing moves the tree between candidates only. */
  readonly candidates?: readonly CandidateMarker[]
  /** Keyboard step in candidate mode: direction in ENU (east, north). */
  readonly onStep?: (east: number, north: number) => void
  readonly treeState: TreeState | null
  readonly committed: Vec3 | null
  readonly draft: Vec3 | null
  readonly editable: boolean
  readonly onDraftChange: (position: Vec3) => void
  readonly siteLabel: string
  /** Placements of evaluated alternative layouts from a stored search result (positions only). */
  readonly overlays?: readonly { readonly id: string; readonly positions: readonly Vec3[]; readonly highlighted: boolean }[]
  /** Camera distance multiplier for "Reset view" and the first framing (view only; 1 = default). */
  readonly framing?: number
}

/**
 * Scene palette (Vision v2 light map). WebGL materials cannot read CSS variables, so these mirror
 * the tokens in styles.css: --scene-bg, --target, --candidate, --lime, --ink and the map key glyphs.
 */
const C = {
  background: '#e6e9e0', ground: '#d3dec6', gridFine: '#9fb39a', gridCoarse: '#7d957a',
  skyLight: '#ffffff', groundLight: '#b6c6ab', sunLight: '#fff4d7',
  crown: '#a5d86a', trunk: '#7a5b3e', ghostCrown: '#7d8f79', ghostTrunk: '#9c8f80', selectedRing: '#13221d',
  target: '#2f7f96', targetEdge: '#256a7e', receiverPoint: '#13221d', sun: '#c58a1c', sunDisc: '#e8b84a',
  obstacle: '#9aa39b', triangles: '#b9bfb6', region: '#4e7a2e',
  candidate: '#24423a', candidateSelected: '#13221d', candidateSelectedDot: '#b7e879',
  option: '#3c6fa8', optionMuted: '#5d7a8c',
} as const

const HOME = new THREE.Vector3(6.5, 6, 8.5)
const toV = (p: readonly number[]) => new THREE.Vector3(...enuToViewer(p))
const STEP_M = 0.1
const BIG_STEP_M = 1

/** One tree from its profile state, in ENU metres: crown ellipsoid and trunk cylinder. */
function buildTree(state: TreeState, ghost: boolean) {
  const group = new THREE.Group()
  const [rx, ry, rz] = state.crown_radii_m
  const crown = new THREE.Mesh(
    new THREE.SphereGeometry(1, 28, 18),
    new THREE.MeshStandardMaterial({ color: ghost ? C.ghostCrown : C.crown, roughness: 0.8, transparent: ghost, opacity: ghost ? 0.28 : 1, depthWrite: !ghost }),
  )
  crown.scale.set(rx, rz, ry) // ENU radii (east, north, up) -> Three (x, y, z) = (east, up, north)
  crown.position.y = state.crown_center_height_m
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(state.trunk_radius_m, state.trunk_radius_m, state.trunk_height_m, 16),
    new THREE.MeshStandardMaterial({ color: ghost ? C.ghostTrunk : C.trunk, roughness: 1, transparent: ghost, opacity: ghost ? 0.28 : 1, depthWrite: !ghost }),
  )
  trunk.position.y = state.trunk_height_m / 2
  group.add(crown, trunk)
  if (!ghost) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(Math.max(rx, ry) * 1.15, Math.max(rx, ry) * 1.3, 40),
      new THREE.MeshBasicMaterial({ color: C.selectedRing, side: THREE.DoubleSide }),
    )
    ring.rotation.x = -Math.PI / 2
    ring.position.y = 0.012
    group.add(ring)
  }
  return group
}

function disposeObject(object: THREE.Object3D) {
  object.traverse(child => {
    if (child instanceof THREE.Mesh || child instanceof THREE.Line) {
      child.geometry.dispose()
      const materials = Array.isArray(child.material) ? child.material : [child.material]
      materials.forEach(m => m.dispose())
    }
  })
}

export default function SiteScene({ scene, candidates = [], onStep, treeState, committed, draft, editable, onDraftChange, siteLabel, overlays = [], framing = 1 }: SiteSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null)
  const northRef = useRef<HTMLSpanElement>(null)
  const world = useRef<{
    scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: OrbitControls; renderer: THREE.WebGLRenderer
    staticGroup: THREE.Group; overlayGroup: THREE.Group; draftTree: THREE.Group | null; ghostTree: THREE.Group | null
    /** Request one render on the next frame (the scene renders on demand, not every frame). */
    invalidate: () => void
  } | null>(null)
  const latest = useRef({ draft, editable, onDraftChange })
  latest.current = { draft, editable, onDraftChange }
  const [state, setState] = useState<SceneState>('loading')
  const [dragging, setDragging] = useState(false)

  // Renderer, camera, controls, ground and pointer editing: created once.
  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, preserveDrawingBuffer: true })
    } catch {
      setState('error')
      return
    }
    // Full-bleed canvas: cap the pixel ratio so high-DPI and GPU-less (software WebGL) machines stay responsive.
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setClearColor(C.background)
    mount.appendChild(renderer.domElement)
    renderer.domElement.setAttribute('aria-hidden', 'true')

    const scene = new THREE.Scene()
    scene.fog = new THREE.Fog(C.background, 30, 70)
    const camera = new THREE.PerspectiveCamera(45, 1, 0.05, 200)
    camera.position.copy(HOME)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.minDistance = 2
    controls.maxDistance = 60
    controls.maxPolarAngle = Math.PI / 2.05
    controls.target.set(0, 0.5, 0)
    const updateNorth = () => {
      const centre = new THREE.Vector3(0, 0, 0).project(camera)
      const north = toV([0, 5, 0]).project(camera)
      const angle = Math.atan2(north.x - centre.x, north.y - centre.y) * 180 / Math.PI
      if (northRef.current) northRef.current.style.transform = `rotate(${angle}deg)`
    }
    controls.addEventListener('change', updateNorth)
    // Render on demand: only after a camera change, a resize or a scene edit. An idle full-bleed
    // canvas otherwise re-renders every frame and starves the main thread without a GPU.
    let dirty = true
    const invalidate = () => { dirty = true }
    controls.addEventListener('change', invalidate)

    scene.add(new THREE.HemisphereLight(C.skyLight, C.groundLight, 2.0))
    const light = new THREE.DirectionalLight(C.sunLight, 1.6)
    light.position.set(-8, 14, 6)
    scene.add(light)

    const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: C.ground, roughness: 1 }))
    ground.rotation.x = -Math.PI / 2
    scene.add(ground)
    const fine = new THREE.GridHelper(40, 40, C.gridFine, C.gridFine)
    fine.position.y = 0.004
    ;(fine.material as THREE.Material).transparent = true
    ;(fine.material as THREE.Material).opacity = 0.35
    const coarse = new THREE.GridHelper(40, 4, C.gridCoarse, C.gridCoarse)
    coarse.position.y = 0.006
    scene.add(fine, coarse)
    const staticGroup = new THREE.Group()
    const overlayGroup = new THREE.Group()
    scene.add(staticGroup, overlayGroup)

    world.current = { scene, camera, controls, renderer, staticGroup, overlayGroup, draftTree: null, ghostTree: null, invalidate }

    // Pointer editing: drag the proposed tree across the ground plane (u = 0).
    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0)
    let grab: THREE.Vector3 | null = null
    const setPointer = (event: PointerEvent) => {
      const rect = renderer.domElement.getBoundingClientRect()
      pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1)
      raycaster.setFromCamera(pointer, camera)
    }
    const onDown = (event: PointerEvent) => {
      const tree = world.current?.draftTree
      if (!tree || !latest.current.editable || !latest.current.draft) return
      setPointer(event)
      if (raycaster.intersectObject(tree, true).length === 0) return
      const hit = new THREE.Vector3()
      if (!raycaster.ray.intersectPlane(plane, hit)) return
      grab = hit.sub(toV(latest.current.draft))
      controls.enabled = false
      renderer.domElement.setPointerCapture(event.pointerId)
      setDragging(true)
    }
    const onMove = (event: PointerEvent) => {
      if (!grab || !latest.current.draft) return
      setPointer(event)
      const hit = new THREE.Vector3()
      if (!raycaster.ray.intersectPlane(plane, hit)) return
      const enu = viewerToEnu(hit.sub(grab).toArray())
      latest.current.onDraftChange(clampPosition([enu[0], enu[1], latest.current.draft[2]]))
    }
    const onUp = (event: PointerEvent) => {
      if (!grab) return
      grab = null
      controls.enabled = true
      if (renderer.domElement.hasPointerCapture(event.pointerId)) renderer.domElement.releasePointerCapture(event.pointerId)
      setDragging(false)
    }
    renderer.domElement.addEventListener('pointerdown', onDown)
    renderer.domElement.addEventListener('pointermove', onMove)
    renderer.domElement.addEventListener('pointerup', onUp)
    renderer.domElement.addEventListener('pointercancel', onUp)

    const observer = new ResizeObserver(() => {
      const width = mount.clientWidth
      const height = mount.clientHeight
      if (!width || !height) return
      renderer.setSize(width, height)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      updateNorth()
      invalidate()
    })
    observer.observe(mount)

    let frame = 0
    const animate = () => {
      frame = requestAnimationFrame(animate)
      controls.update() // dispatches 'change' (and so invalidates) while the camera is moving or damping
      if (!dirty) return
      dirty = false
      renderer.render(scene, camera)
    }
    animate()
    updateNorth()
    setState('ready')
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      renderer.domElement.removeEventListener('pointerdown', onDown)
      renderer.domElement.removeEventListener('pointermove', onMove)
      renderer.domElement.removeEventListener('pointerup', onUp)
      renderer.domElement.removeEventListener('pointercancel', onUp)
      controls.removeEventListener('change', updateNorth)
      controls.removeEventListener('change', invalidate)
      controls.dispose()
      disposeObject(scene)
      world.current = null
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  // Verified scene inputs only: reference declaration (receiver, sun direction, obstacles) or
  // physical scene (receiver samples, static triangles, planting regions), plus catalogue candidates.
  const candidateKey = JSON.stringify(candidates)
  useEffect(() => {
    const w = world.current
    if (!w) return
    w.staticGroup.children.slice().forEach(child => { w.staticGroup.remove(child); disposeObject(child) })
    if (scene?.kind === 'reference') {
      const declaration = scene.declaration
      const radius = Math.sqrt(declaration.receiver_area_m2 / Math.PI)
      const receiver = new THREE.Mesh(
        new THREE.CircleGeometry(radius, 48),
        new THREE.MeshBasicMaterial({ color: C.target, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false }),
      )
      receiver.rotation.x = -Math.PI / 2
      receiver.position.copy(toV(declaration.receiver_point)).add(new THREE.Vector3(0, 0.01, 0))
      const edge = new THREE.Mesh(new THREE.RingGeometry(radius * 0.97, radius, 48), new THREE.MeshBasicMaterial({ color: C.targetEdge, side: THREE.DoubleSide }))
      edge.rotation.x = -Math.PI / 2
      edge.position.copy(receiver.position).add(new THREE.Vector3(0, 0.002, 0))
      const point = new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 12), new THREE.MeshBasicMaterial({ color: C.receiverPoint }))
      point.position.copy(toV(declaration.receiver_point))
      w.staticGroup.add(receiver, edge, point)
      if (declaration.above_horizon) {
        const start = toV(declaration.receiver_point)
        const end = start.clone().add(toV(declaration.sun_direction).normalize().multiplyScalar(7))
        const ray = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([start, end]),
          new THREE.LineDashedMaterial({ color: C.sun, dashSize: 0.25, gapSize: 0.15 }),
        )
        ray.computeLineDistances()
        const sun = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 14), new THREE.MeshBasicMaterial({ color: C.sunDisc }))
        sun.position.copy(end)
        w.staticGroup.add(ray, sun)
      }
      declaration.obstacle_ellipsoids.forEach(([centre, radii]) => {
        const obstacle = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({ color: C.obstacle, roughness: 1 }))
        obstacle.scale.set(radii[0], radii[2], radii[1])
        obstacle.position.copy(toV(centre))
        w.staticGroup.add(obstacle)
      })
    } else if (scene?.kind === 'physical') {
      const p = scene.scene
      // Receiver samples: one tile per sample, sized to its represented area, on its own normal plane (flat here).
      const tileMaterial = new THREE.MeshBasicMaterial({ color: C.target, transparent: true, opacity: 0.4, side: THREE.DoubleSide, depthWrite: false })
      const tiles = new THREE.InstancedMesh(new THREE.PlaneGeometry(1, 1), tileMaterial, p.samples.length)
      const m = new THREE.Matrix4()
      const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI / 2, 0, 0))
      p.samples.forEach((sample, i) => {
        const side = Math.sqrt(sample.area_m2) * 0.92
        m.compose(toV(sample.position_enu_m).add(new THREE.Vector3(0, 0.01, 0)), q, new THREE.Vector3(side, side, 1))
        tiles.setMatrixAt(i, m)
      })
      w.staticGroup.add(tiles)
      if (p.triangles.length) {
        const positions = new Float32Array(p.triangles.flatMap(t => t.vertices_enu_m.flatMap(v => toV(v).toArray())))
        const g = new THREE.BufferGeometry()
        g.setAttribute('position', new THREE.BufferAttribute(positions, 3))
        g.computeVertexNormals()
        w.staticGroup.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: C.triangles, roughness: 1, side: THREE.DoubleSide })))
      }
      Object.values(p.regions).forEach(polygon => {
        const pts = polygon.map(([e, n]) => toV([e, n, p.flat_ground_z_m]).add(new THREE.Vector3(0, 0.02, 0)))
        const line = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineDashedMaterial({ color: C.region, dashSize: 0.4, gapSize: 0.25 }))
        line.computeLineDistances()
        w.staticGroup.add(line)
      })
    }
    for (const c of candidates) {
      const marker = new THREE.Mesh(
        new THREE.RingGeometry(0.22, 0.34, 32),
        new THREE.MeshBasicMaterial({ color: c.selected ? C.candidateSelected : C.candidate, side: THREE.DoubleSide }),
      )
      marker.rotation.x = -Math.PI / 2
      marker.position.copy(toV(c.position)).add(new THREE.Vector3(0, 0.03, 0))
      const dot = new THREE.Mesh(new THREE.CircleGeometry(0.08, 16), new THREE.MeshBasicMaterial({ color: c.selected ? C.candidateSelectedDot : C.candidate, side: THREE.DoubleSide }))
      dot.rotation.x = -Math.PI / 2
      dot.position.copy(marker.position)
      w.staticGroup.add(marker, dot)
    }
    w.invalidate()
  }, [scene, candidateKey, state]) // eslint-disable-line react-hooks/exhaustive-deps

  // Alternative layouts from a stored search result: a ring per placement; the highlighted one also gets crowns.
  const overlayKey = JSON.stringify(overlays)
  useEffect(() => {
    const w = world.current
    if (!w) return
    w.overlayGroup.children.slice().forEach(child => { w.overlayGroup.remove(child); disposeObject(child) })
    for (const layout of overlays) {
      for (const p of layout.positions) {
        const r = treeState ? Math.max(treeState.crown_radii_m[0], treeState.crown_radii_m[1]) : 0.5
        const ring = new THREE.Mesh(
          new THREE.RingGeometry(r * 0.9, r * 1.05, 40),
          new THREE.MeshBasicMaterial({ color: layout.highlighted ? C.option : C.optionMuted, side: THREE.DoubleSide, transparent: true, opacity: layout.highlighted ? 0.95 : 0.45 }),
        )
        ring.rotation.x = -Math.PI / 2
        ring.position.copy(toV(p)).add(new THREE.Vector3(0, 0.015, 0))
        w.overlayGroup.add(ring)
        if (layout.highlighted && treeState) {
          const crown = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({ color: C.option, transparent: true, opacity: 0.35, depthWrite: false }))
          crown.scale.set(treeState.crown_radii_m[0], treeState.crown_radii_m[2], treeState.crown_radii_m[1])
          crown.position.copy(toV(p)).add(new THREE.Vector3(0, treeState.crown_center_height_m, 0))
          w.overlayGroup.add(crown)
        }
      }
    }
    w.invalidate()
  }, [overlayKey, treeState, state]) // eslint-disable-line react-hooks/exhaustive-deps

  // Proposed tree (draft) and, when moved, a ghost at the last committed position.
  useEffect(() => {
    const w = world.current
    if (!w) return
    for (const key of ['draftTree', 'ghostTree'] as const) {
      const old = w[key]
      if (old) { w.scene.remove(old); disposeObject(old); w[key] = null }
    }
    w.invalidate()
    if (!treeState || !draft) return
    const tree = buildTree(treeState, false)
    tree.position.copy(toV(draft))
    w.scene.add(tree)
    w.draftTree = tree
    if (committed && (committed[0] !== draft[0] || committed[1] !== draft[1] || committed[2] !== draft[2])) {
      const ghost = buildTree(treeState, true)
      ghost.position.copy(toV(committed))
      w.scene.add(ghost)
      w.ghostTree = ghost
    }
  }, [treeState, draft, committed, state])

  /** Frame the declared receiver and the proposed tree together, keeping the default viewing angle. */
  const frameAll = () => {
    const w = world.current
    if (!w) return
    const sceneVolume = scene?.kind === 'reference' ? [toV(scene.declaration.receiver_point)]
      : scene?.kind === 'physical' ? scene.scene.samples.map(x => toV(x.position_enu_m)) : [new THREE.Vector3()]
    const points = [...sceneVolume, ...candidates.map(c => toV(c.position)), ...(draft ? [toV(draft)] : [])]
    const box = new THREE.Box3().setFromPoints(points)
    const centre = box.getCenter(new THREE.Vector3()).add(new THREE.Vector3(0, 0.5, 0))
    const span = box.getSize(new THREE.Vector3()).length()
    const scale = Math.max(1, span / 7) * framing
    w.controls.target.copy(centre)
    w.camera.position.copy(centre).add(HOME.clone().multiplyScalar(scale))
    w.controls.update()
  }
  const framed = useRef(false)
  useEffect(() => {
    if (state !== 'ready' || framed.current || !draft || !scene) return
    framed.current = true
    frameAll()
  }, [state, draft, scene]) // eslint-disable-line react-hooks/exhaustive-deps

  const moveCamera = (action: CameraAction) => {
    const w = world.current
    if (!w) return
    const { camera, controls } = w
    if (action === 'reset') {
      frameAll()
      return
    } else if (action === 'tree') {
      if (!draft) return
      const focus = toV(draft).add(new THREE.Vector3(0, 0.5, 0))
      camera.position.add(focus.clone().sub(controls.target))
      controls.target.copy(focus)
    } else if (action === 'zoomIn' || action === 'zoomOut') {
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(action === 'zoomIn' ? 0.78 : 1.28)
      offset.clampLength(controls.minDistance, controls.maxDistance)
      camera.position.copy(controls.target).add(offset)
    } else {
      const offset = camera.position.clone().sub(controls.target)
      offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), action === 'left' ? -Math.PI / 8 : Math.PI / 8)
      camera.position.copy(controls.target).add(offset)
    }
    controls.update()
  }

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!editable || !draft) return
    const step = event.shiftKey ? BIG_STEP_M : STEP_M
    const moves: Record<string, [number, number]> = { ArrowUp: [0, step], ArrowDown: [0, -step], ArrowRight: [step, 0], ArrowLeft: [-step, 0] }
    const move = moves[event.key]
    if (!move) return
    event.preventDefault()
    if (onStep) onStep(Math.sign(move[0]), Math.sign(move[1]))
    else onDraftChange(nudge(draft, move[0], move[1]))
  }

  return (
    <div
      className={`scene-wrap${dragging ? ' dragging' : ''}`}
      tabIndex={0}
      role="group"
      aria-label={`3D site view. ${!editable ? 'Editing unavailable.' : onStep ? 'Arrow keys move the proposed tree to the nearest catalogue position in that direction; up is north.' : 'Arrow keys move the proposed tree 0.1 m (Shift: 1 m); up is north.'}`}
      onKeyDown={onKeyDown}
    >
      <div className="scene-canvas" ref={mountRef} />
      <div className="scene-topline"><span className="pill pill-lime">{siteLabel}</span><span className="scene-scale">ENU metres · grid 1 m</span></div>
      {state === 'loading' && <div className="scene-message" role="status">Loading scene…</div>}
      {state === 'error' && <div className="scene-message" role="alert">3D view unavailable on this device. Use the position fields to edit the proposed tree.</div>}
      {state === 'ready' && !scene && <div className="scene-message" role="status">No hash-checked site geometry to draw yet.</div>}
      <div className="north-indicator" aria-label="North direction in the current camera view"><span ref={northRef}>↑</span> N</div>
      <div className="scene-toolbar" aria-label="Camera controls">
        <button type="button" onClick={() => moveCamera('left')} aria-label="Orbit camera left">↶</button>
        <button type="button" onClick={() => moveCamera('right')} aria-label="Orbit camera right">↷</button>
        <button type="button" onClick={() => moveCamera('zoomIn')} aria-label="Zoom in">+</button>
        <button type="button" onClick={() => moveCamera('zoomOut')} aria-label="Zoom out">−</button>
        <button type="button" onClick={() => moveCamera('tree')} disabled={!draft}>Find tree</button>
        <button type="button" onClick={() => moveCamera('reset')}>Reset view</button>
      </div>
      <p className="sr-only">
        {scene?.kind === 'reference'
          ? `Target receiver sample at east ${scene.declaration.receiver_point[0]} m, north ${scene.declaration.receiver_point[1]} m representing ${scene.declaration.receiver_area_m2} square metres. ${draft ? `Proposed tree at east ${draft[0]} m, north ${draft[1]} m.` : ''} A dashed line shows the declared sun direction used by the evaluator; it is an input, not a result.`
          : scene?.kind === 'physical'
            ? `${scene.scene.samples.length} receiver samples, ${scene.scene.triangles.length} static triangles, ${Object.keys(scene.scene.regions).length} planting region(s) and ${candidates.length} catalogue positions. ${draft ? `Proposed tree at east ${draft[0]} m, north ${draft[1]} m.` : ''}`
            : 'No hash-checked site geometry is available.'}
      </p>
    </div>
  )
}
