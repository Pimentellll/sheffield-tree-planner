import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import type { SyntheticDeclaration } from '../api/session'
import type { TreeState, Vec3 } from '../api/types'
import { clampPosition, nudge } from '../planning/evaluation'
import { enuToViewer, viewerToEnu } from './transform'

type SceneState = 'loading' | 'ready' | 'error'
type CameraAction = 'left' | 'right' | 'zoomIn' | 'zoomOut' | 'reset' | 'tree'

export interface SiteSceneProps {
  readonly declaration: SyntheticDeclaration | null
  readonly treeState: TreeState | null
  readonly committed: Vec3 | null
  readonly draft: Vec3 | null
  readonly editable: boolean
  readonly onDraftChange: (position: Vec3) => void
  readonly siteLabel: string
  /** Placements of evaluated alternative layouts from a stored search result (positions only). */
  readonly overlays?: readonly { readonly id: string; readonly positions: readonly Vec3[]; readonly highlighted: boolean }[]
}

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
    new THREE.MeshStandardMaterial({ color: ghost ? '#c9d8c3' : '#7fb33f', roughness: 0.8, transparent: ghost, opacity: ghost ? 0.28 : 1, depthWrite: !ghost }),
  )
  crown.scale.set(rx, rz, ry) // ENU radii (east, north, up) -> Three (x, y, z) = (east, up, north)
  crown.position.y = state.crown_center_height_m
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(state.trunk_radius_m, state.trunk_radius_m, state.trunk_height_m, 16),
    new THREE.MeshStandardMaterial({ color: ghost ? '#d9cfc0' : '#8a6d4f', roughness: 1, transparent: ghost, opacity: ghost ? 0.28 : 1, depthWrite: !ghost }),
  )
  trunk.position.y = state.trunk_height_m / 2
  group.add(crown, trunk)
  if (!ghost) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(Math.max(rx, ry) * 1.15, Math.max(rx, ry) * 1.3, 40),
      new THREE.MeshBasicMaterial({ color: '#b7e879', side: THREE.DoubleSide }),
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

export default function SiteScene({ declaration, treeState, committed, draft, editable, onDraftChange, siteLabel, overlays = [] }: SiteSceneProps) {
  const mountRef = useRef<HTMLDivElement>(null)
  const northRef = useRef<HTMLSpanElement>(null)
  const world = useRef<{
    scene: THREE.Scene; camera: THREE.PerspectiveCamera; controls: OrbitControls; renderer: THREE.WebGLRenderer
    staticGroup: THREE.Group; overlayGroup: THREE.Group; draftTree: THREE.Group | null; ghostTree: THREE.Group | null
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
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setClearColor('#142820')
    mount.appendChild(renderer.domElement)
    renderer.domElement.setAttribute('aria-hidden', 'true')

    const scene = new THREE.Scene()
    scene.fog = new THREE.Fog('#142820', 30, 70)
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

    scene.add(new THREE.HemisphereLight('#d2e8e5', '#58755f', 2.2))
    const light = new THREE.DirectionalLight('#fff4d7', 1.6)
    light.position.set(-8, 14, 6)
    scene.add(light)

    const ground = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ color: '#2f4f3e', roughness: 1 }))
    ground.rotation.x = -Math.PI / 2
    scene.add(ground)
    const fine = new THREE.GridHelper(40, 40, '#5d7d68', '#5d7d68')
    fine.position.y = 0.004
    ;(fine.material as THREE.Material).transparent = true
    ;(fine.material as THREE.Material).opacity = 0.35
    const coarse = new THREE.GridHelper(40, 4, '#a8c4a6', '#a8c4a6')
    coarse.position.y = 0.006
    scene.add(fine, coarse)
    const staticGroup = new THREE.Group()
    const overlayGroup = new THREE.Group()
    scene.add(staticGroup, overlayGroup)

    world.current = { scene, camera, controls, renderer, staticGroup, overlayGroup, draftTree: null, ghostTree: null }

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
    })
    observer.observe(mount)

    let frame = 0
    const animate = () => {
      frame = requestAnimationFrame(animate)
      controls.update()
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
      controls.dispose()
      disposeObject(scene)
      world.current = null
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  // Declared synthetic inputs: target receiver sample, declared sun direction, obstacles.
  useEffect(() => {
    const w = world.current
    if (!w) return
    w.staticGroup.children.slice().forEach(child => { w.staticGroup.remove(child); disposeObject(child) })
    if (!declaration) return
    const radius = Math.sqrt(declaration.receiver_area_m2 / Math.PI)
    const receiver = new THREE.Mesh(
      new THREE.CircleGeometry(radius, 48),
      new THREE.MeshBasicMaterial({ color: '#62afc2', transparent: true, opacity: 0.55, side: THREE.DoubleSide, depthWrite: false }),
    )
    receiver.rotation.x = -Math.PI / 2
    receiver.position.copy(toV(declaration.receiver_point)).add(new THREE.Vector3(0, 0.01, 0))
    const edge = new THREE.Mesh(new THREE.RingGeometry(radius * 0.97, radius, 48), new THREE.MeshBasicMaterial({ color: '#a6dce7', side: THREE.DoubleSide }))
    edge.rotation.x = -Math.PI / 2
    edge.position.copy(receiver.position).add(new THREE.Vector3(0, 0.002, 0))
    const point = new THREE.Mesh(new THREE.SphereGeometry(0.06, 16, 12), new THREE.MeshBasicMaterial({ color: '#e6f6fa' }))
    point.position.copy(toV(declaration.receiver_point))
    w.staticGroup.add(receiver, edge, point)
    if (declaration.above_horizon) {
      const start = toV(declaration.receiver_point)
      const end = start.clone().add(toV(declaration.sun_direction).normalize().multiplyScalar(7))
      const ray = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([start, end]),
        new THREE.LineDashedMaterial({ color: '#f1d27a', dashSize: 0.25, gapSize: 0.15 }),
      )
      ray.computeLineDistances()
      const sun = new THREE.Mesh(new THREE.SphereGeometry(0.28, 20, 14), new THREE.MeshBasicMaterial({ color: '#f1d27a' }))
      sun.position.copy(end)
      w.staticGroup.add(ray, sun)
    }
    declaration.obstacle_ellipsoids.forEach(([centre, radii]) => {
      const obstacle = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({ color: '#7d8a7f', roughness: 1 }))
      obstacle.scale.set(radii[0], radii[2], radii[1])
      obstacle.position.copy(toV(centre))
      w.staticGroup.add(obstacle)
    })
  }, [declaration, state])

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
          new THREE.MeshBasicMaterial({ color: layout.highlighted ? '#9fd3ff' : '#c9d8c3', side: THREE.DoubleSide, transparent: true, opacity: layout.highlighted ? 0.95 : 0.45 }),
        )
        ring.rotation.x = -Math.PI / 2
        ring.position.copy(toV(p)).add(new THREE.Vector3(0, 0.015, 0))
        w.overlayGroup.add(ring)
        if (layout.highlighted && treeState) {
          const crown = new THREE.Mesh(new THREE.SphereGeometry(1, 20, 14), new THREE.MeshStandardMaterial({ color: '#9fd3ff', transparent: true, opacity: 0.45, depthWrite: false }))
          crown.scale.set(treeState.crown_radii_m[0], treeState.crown_radii_m[2], treeState.crown_radii_m[1])
          crown.position.copy(toV(p)).add(new THREE.Vector3(0, treeState.crown_center_height_m, 0))
          w.overlayGroup.add(crown)
        }
      }
    }
  }, [overlayKey, treeState, state]) // eslint-disable-line react-hooks/exhaustive-deps

  // Proposed tree (draft) and, when moved, a ghost at the last committed position.
  useEffect(() => {
    const w = world.current
    if (!w) return
    for (const key of ['draftTree', 'ghostTree'] as const) {
      const old = w[key]
      if (old) { w.scene.remove(old); disposeObject(old); w[key] = null }
    }
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

  const moveCamera = (action: CameraAction) => {
    const w = world.current
    if (!w) return
    const { camera, controls } = w
    if (action === 'reset') {
      camera.position.copy(HOME)
      controls.target.set(0, 0.5, 0)
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
    onDraftChange(nudge(draft, move[0], move[1]))
  }

  return (
    <div
      className={`scene-wrap${dragging ? ' dragging' : ''}`}
      tabIndex={0}
      role="group"
      aria-label={`3D site view. ${editable ? 'Arrow keys move the proposed tree 0.1 m (Shift: 1 m); up is north.' : 'Editing unavailable.'}`}
      onKeyDown={onKeyDown}
    >
      <div className="scene-canvas" ref={mountRef} />
      <div className="scene-topline"><span className="pill pill-lime">{siteLabel}</span><span className="scene-scale">ENU metres · grid 1 m</span></div>
      {state === 'loading' && <div className="scene-message" role="status">Loading scene…</div>}
      {state === 'error' && <div className="scene-message" role="alert">3D view unavailable on this device. Use the position fields to edit the proposed tree.</div>}
      {state === 'ready' && !declaration && <div className="scene-message" role="status">No verified site geometry to draw yet.</div>}
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
        {declaration
          ? `Target receiver sample at east ${declaration.receiver_point[0]} m, north ${declaration.receiver_point[1]} m representing ${declaration.receiver_area_m2} square metres. ${draft ? `Proposed tree at east ${draft[0]} m, north ${draft[1]} m.` : ''} A dashed line shows the declared sun direction used by the evaluator; it is an input, not a result.`
          : 'No verified site geometry is available.'}
      </p>
    </div>
  )
}
