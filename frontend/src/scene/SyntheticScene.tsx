import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import type { M2Session } from '../../../generated/contracts'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

type SceneState = 'loading' | 'ready' | 'error'
type CameraAction = 'left' | 'right' | 'zoomIn' | 'zoomOut' | 'reset'

// Provisional display transform only: ENU (east, north, up) metres -> Three (x, y, z).
// [x, y, z]viewer = [east, up, -north]. The backend SiteBundle will own this matrix.
const toViewer = (east: number, north: number, up: number) => new THREE.Vector3(east, up, -north)

function makeTree(east: number, north: number, radius: number) {
  const tree = new THREE.Group()
  tree.position.copy(toViewer(east, north, 0))
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(0.7, 0.85, 5, 8),
    new THREE.MeshStandardMaterial({ color: '#9c8568', roughness: 1 }),
  )
  trunk.position.y = 2.5
  const crown = new THREE.Mesh(
    new THREE.IcosahedronGeometry(radius, 1),
    new THREE.MeshStandardMaterial({ color: '#527a55', roughness: 0.9, flatShading: true }),
  )
  crown.scale.y = 0.7
  crown.position.y = 6.8
  tree.add(trunk, crown)
  return tree
}

function makeTarget() {
  const shape = new THREE.Shape()
  shape.moveTo(-38, -16)
  shape.lineTo(28, -16)
  shape.lineTo(35, 15)
  shape.lineTo(-34, 19)
  shape.closePath()
  const mesh = new THREE.Mesh(
    new THREE.ShapeGeometry(shape),
    new THREE.MeshBasicMaterial({ color: '#62afc2', transparent: true, opacity: 0.26, side: THREE.DoubleSide, depthWrite: false }),
  )
  mesh.rotation.x = -Math.PI / 2
  mesh.position.y = 0.15
  const edge = new THREE.LineLoop(
    new THREE.BufferGeometry().setFromPoints(shape.getPoints().map(p => new THREE.Vector3(p.x, 0.2, -p.y))),
    new THREE.LineBasicMaterial({ color: '#a6dce7' }),
  )
  return [mesh, edge]
}

export default function SyntheticScene({ session }: { session: M2Session | null }) {
  const mountRef = useRef<HTMLDivElement>(null)
  const northRef = useRef<HTMLSpanElement>(null)
  const controllerRef = useRef<{ camera: THREE.PerspectiveCamera; controls: OrbitControls } | null>(null)
  const [state, setState] = useState<SceneState>('loading')

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    let renderer: THREE.WebGLRenderer
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
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
    scene.fog = new THREE.Fog('#142820', 145, 310)
    const camera = new THREE.PerspectiveCamera(47, 1, 0.1, 500)
    if (session) { camera.up.set(0, 0, 1); camera.position.set(9, -12, 10) } else camera.position.set(87, 105, 118)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.minDistance = session ? 2 : 38
    controls.maxDistance = session ? 60 : 280
    controls.maxPolarAngle = Math.PI / 2.12
    controls.target.set(0, 0, 0)
    controllerRef.current = { camera, controls }
    const updateNorth = () => {
      const centre = new THREE.Vector3(0, 0, 0).project(camera)
      const north = (session ? new THREE.Vector3(0, 20, 0) : new THREE.Vector3(0, 0, -20)).project(camera)
      const angle = Math.atan2(north.x - centre.x, north.y - centre.y) * 180 / Math.PI
      if (northRef.current) northRef.current.style.transform = `rotate(${angle}deg)`
    }
    controls.addEventListener('change', updateNorth)
    updateNorth()

    scene.add(new THREE.HemisphereLight('#d2e8e5', '#58755f', 2.1))
    const sun = new THREE.DirectionalLight('#fff4d7', 2.2)
    sun.position.set(-45, 100, 35)
    scene.add(sun)

    if (!session) {
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(150, 110),
      new THREE.MeshStandardMaterial({ color: '#365b45', roughness: 1 }),
    )
    ground.rotation.x = -Math.PI / 2
    scene.add(ground)

    const site = new THREE.Mesh(
      new THREE.PlaneGeometry(120, 80),
      new THREE.MeshStandardMaterial({ color: '#b5b7a5', roughness: 1 }),
    )
    site.rotation.x = -Math.PI / 2
    site.position.y = 0.05
    scene.add(site)

    const path = new THREE.Mesh(
      new THREE.PlaneGeometry(125, 8),
      new THREE.MeshStandardMaterial({ color: '#ded8c3', roughness: 1 }),
    )
    path.rotation.x = -Math.PI / 2
    path.rotation.z = -0.11
    path.position.set(0, 0.1, 23)
    scene.add(path)

    const [targetFill, targetEdge] = makeTarget()
    scene.add(targetFill, targetEdge)
    ;[[-46, -23, 7], [-24, 27, 9], [31, -22, 8], [49, 26, 6], [-51, 24, 6]].forEach(([east, north, radius]) => {
      scene.add(makeTree(east, north, radius))
    })

    const grid = new THREE.GridHelper(120, 12, '#8a9d86', '#8a9d86')
    grid.position.y = 0.12
    grid.material.transparent = true
    grid.material.opacity = 0.22
    scene.add(grid)

    } else {
      const matrix = new THREE.Matrix4().set(...session.site.analysis_to_viewer.flat() as [number, number, number, number, number, number, number, number, number, number, number, number, number, number, number, number])
      const inputs = new THREE.Group()
      inputs.applyMatrix4(matrix)
      const grid = new THREE.GridHelper(12, 12, '#8a9d86', '#8a9d86')
      grid.rotation.x = Math.PI / 2
      inputs.add(grid)
      const placement = session.layout.placements[0]
      const stateName = session.scenario.input.evaluation_cases[0]?.profile_state
      const profile = session.profile.states[stateName]
      if (placement && profile) {
        const tree = new THREE.Group()
        tree.position.set(...placement.position_enu_m)
        const trunk = new THREE.Mesh(new THREE.CylinderGeometry(profile.trunk_radius_m, profile.trunk_radius_m, profile.trunk_height_m, 12), new THREE.MeshStandardMaterial({ color: '#9c8568' }))
        trunk.rotation.x = Math.PI / 2
        trunk.position.z = profile.trunk_height_m / 2
        const crown = new THREE.Mesh(new THREE.SphereGeometry(1, 24, 16), new THREE.MeshStandardMaterial({ color: '#86ba65', roughness: 0.9 }))
        crown.scale.set(...profile.crown_radii_m)
        crown.position.z = profile.crown_center_height_m
        tree.add(trunk, crown); inputs.add(tree)
      }
      const receiver = new THREE.Mesh(new THREE.SphereGeometry(0.16, 12, 8), new THREE.MeshBasicMaterial({ color: '#a6dce7' }))
      receiver.position.set(...session.scene.receiver_point); inputs.add(receiver)
      for (const [centre, radii] of session.scene.obstacle_ellipsoids) {
        const obstacle = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 12), new THREE.MeshStandardMaterial({ color: '#879080' }))
        obstacle.position.set(...centre); obstacle.scale.set(...radii); inputs.add(obstacle)
      }
      const direction = new THREE.Vector3(...session.scene.sun_direction)
      if (direction.lengthSq() > 0) inputs.add(new THREE.ArrowHelper(direction.clone().normalize(), new THREE.Vector3(...session.scene.receiver_point), 2, '#e6d68a'))
      scene.add(inputs)
    }
    const observer = new ResizeObserver(() => {
      const width = mount.clientWidth
      const height = mount.clientHeight
      if (!width || !height) return
      renderer.setSize(width, height)
      camera.aspect = width / height
      camera.updateProjectionMatrix()
    })
    observer.observe(mount)

    let frame = 0
    const animate = () => {
      frame = requestAnimationFrame(animate)
      controls.update()
      renderer.render(scene, camera)
    }
    animate()
    setState('ready')
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      controllerRef.current = null
      controls.dispose()
      controls.removeEventListener('change', updateNorth)
      scene.traverse(object => {
        if (object instanceof THREE.Mesh || object instanceof THREE.LineLoop) {
          object.geometry.dispose()
          const materials = Array.isArray(object.material) ? object.material : [object.material]
          materials.forEach(material => material.dispose())
        }
      })
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [session])

  const moveCamera = (action: CameraAction) => {
    const current = controllerRef.current
    if (!current) return
    const { camera, controls } = current
    if (action === 'reset') {
      if (session) camera.position.set(9, -12, 10)
      else camera.position.set(87, 105, 118)
      controls.target.set(0, 0, 0)
    } else if (action === 'zoomIn' || action === 'zoomOut') {
      const factor = action === 'zoomIn' ? 0.78 : 1.28
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(factor)
      offset.clampLength(session ? 2 : 38, session ? 60 : 280)
      camera.position.copy(controls.target).add(offset)
    } else {
      const offset = camera.position.clone().sub(controls.target)
      offset.applyAxisAngle(camera.up, action === 'left' ? -Math.PI / 8 : Math.PI / 8)
      camera.position.copy(controls.target).add(offset)
    }
    controls.update()
  }

  return (
    <div className="scene-wrap">
      <div className="scene-canvas" ref={mountRef} />
      <div className="scene-topline"><span className="pill pill-lime">SYNTHETIC TEST SITE</span><span className="scene-scale">Local ENU · metres</span></div>
      {state === 'loading' && <div className="scene-message" role="status">Loading scene…</div>}
      {state === 'error' && <div className="scene-message" role="alert">3D view unavailable on this device. {session ? 'The reference contains one synthetic tree and one weighted receiver point.' : 'The fixture contains five illustrative trees and a target region.'}</div>}
      <div className="north-indicator" aria-label="North direction in the current camera view"><span ref={northRef}>↑</span> N</div>
      <div className="scene-toolbar" aria-label="Camera controls">
        <button type="button" onClick={() => moveCamera('left')} aria-label="Orbit camera left">↶</button>
        <button type="button" onClick={() => moveCamera('right')} aria-label="Orbit camera right">↷</button>
        <button type="button" onClick={() => moveCamera('zoomIn')} aria-label="Zoom in">+</button>
        <button type="button" onClick={() => moveCamera('zoomOut')} aria-label="Zoom out">−</button>
        <button type="button" onClick={() => moveCamera('reset')}>Reset view</button>
      </div>
      <p className="sr-only">{session ? 'One synthetic tree, a weighted receiver point and the chosen sun direction. Camera buttons provide a keyboard alternative.' : <>Synthetic scene preview. Drag to orbit, scroll to zoom, and right drag to pan. Camera buttons provide a keyboard alternative. Green crowns show five illustrative existing trees. A blue outlined region marks an illustrative target, not an evaluated area.</>}</p>
    </div>
  )
}
