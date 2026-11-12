# CANOPY frontend foundation

STP-007 work in progress on `agent/alex`. This is an interface fixture, not a Sheffield site or a simulator.

## Local run

Requires Node.js 20.19+ or 22.12+.

```powershell
npm.cmd install
npm.cmd run dev
```

Open the URL printed by Vite. `npm.cmd run build` checks TypeScript and creates a static bundle.

With the dev server running, `npm.cmd run test:browser` checks the desktop and 390px layouts, navigation, scene rendering and keyboard camera control. Set `CANOPY_BROWSER` to a local Chromium/Edge executable if it is not in the standard Windows Edge location. Screenshots are written to the ignored `artifacts/` directory.

## Current boundary

- The garden geometry, five existing trees and target outline are synthetic UI inputs. No result number is provided.
- The backend status and disabled evaluation action are deliberate until Ben's generated API types and evaluator are available.
- A provisional display transform maps ENU `(east, north, up)` metres to Three `(x, y, z) = (east, up, -north)`. Its 4×4 row-major matrix is `[1,0,0,0, 0,0,1,0, 0,-1,0,0, 0,0,0,1]` for column vectors. It must be checked against an accepted SiteBundle and Arnav's known-point proof before real geometry is rendered.
- The forest, pine, ivory and lime palette follows the unmerged PR #4 design proposal provisionally. No exported prototype art or external font files are bundled.
- Orbit, zoom and pan use Three.js OrbitControls. Focusable camera buttons provide orbit, zoom and reset alternatives. The scene has a text description for screen readers.
