# CANOPY local synthetic UI integration

This isolated local integration uses Alex's frontend snapshot `7b67722ac31e6a46f91f8d065cceeca08917d7a9` and Ben's backend baseline `7d86c78f53ae00b4861c3530e89a7f6304c0de41`. The original branches and PR45 are not changed. It is a real numerical reference in a synthetic one-tree scene, not a Sheffield site, search planner or scientific/planting acceptance.

## Disconnected fixture preview

Requires Node.js 20.19+ or 22.12+.

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
npm.cmd run dev
```

Open the URL printed by Vite. `npm.cmd run build` checks TypeScript and creates a static bundle.

With the dev server running, `npm.cmd run test:browser` checks the desktop and 390px layouts, navigation, scene rendering and keyboard camera control. Set `CANOPY_BROWSER` to a local Chromium/Edge executable if it is not in the standard Windows Edge location. Screenshots are written to the ignored `artifacts/` directory.

## Real local reference demo

Verified on Windows with Node24 and Python3.11; Node24 is required for the native TypeScript guard-test command. From the repository root, with `uv` installed:

```powershell
uv sync --frozen --extra dev
npm.cmd ci --prefix frontend --ignore-scripts --no-audit --no-fund
npm.cmd --prefix frontend run build
.venv/Scripts/python.exe -m tree_planner.evaluators.ui_demo `
    --workspace ../m2-reference-new `
    --numerical-source ../repo-numerical-inputs `
    --frontend-dist frontend/dist
```

The numerical checkout must contain exact commit `33493a327a99e5de2e579b5c3070ada137047c7e`; substitute its actual path. Source hashes are checked by the loader. The private workspace must be fresh and outside the public frontend build. Open the printed loopback URL; Ctrl+C stops the owned server and worker. The built UI and API share one origin; no CORS wildcard, proxy or remote service is needed. The Python wheel contains the harness, but not a prebuilt frontend: build `frontend/dist` explicitly from this source checkout/source distribution.

The connected view uses the actual layout, profile, receiver point, chosen sun and SiteBundle transform. **Evaluate planting** submits a real asynchronous job. It displays the actual geometric additional shade, run ID, accepted revision and fingerprint. **Reference placement** and **Missed-tree placement** create real new layouts and human-accepted revisions; the latter yields valid zero for this specific reference. Failure or superseded selection removes the old metric. External changes are observed on the next polling pass, not instantaneously.

The receiver is a weighted point sample with declared represented area, not a surveyed target polygon. The one opaque crown/trunk and analytically chosen sun are illustrative inputs; the result is a genuine calculation on those inputs. Feasibility, cost, search, real geography, solar-position accuracy and field performance remain unvalidated. Other screens still require evidence.

## Repeatable checks

From the repository root after the commands above:

```powershell
npm.cmd --prefix frontend run test:client
$env:CANOPY_NUMERICS_SOURCE = (Resolve-Path '../repo-numerical-inputs').Path
npm.cmd --prefix frontend run test:m2
```

`test:m2` starts its own loopback Python server and headless Edge, verifies positive/zero results against stored actual runs, holds an unaltered old HTTP completion to test stale suppression, corrupts/restores only its generated asset, checks failure/recovery and mobile overflow, then closes its browser/server/worker and verifies the port is closed. It creates a fresh ignored `frontend/artifacts/m2-*` receipt, HTTP trace and screenshots. It never substitutes successful result bodies. `CANOPY_BROWSER` may select another installed Chromium executable. `CANOPY_PYTHON` may select another installed package environment; `CANOPY_M2_INSTALLED_ONLY=1` uses Python `-I` without source `PYTHONPATH` for clean-wheel proof. `CANOPY_M2_EVIDENCE` selects a fresh proof directory.

## Original fixture and shared boundaries

- In disconnected Vite preview, five trees and the target outline remain labelled UI fixtures, with evaluation disabled and no number. They are not shown alongside the connected one-tree calculation.
- The connected view uses the actual site `analysis_to_viewer` matrix and ENU z-up. The original disconnected fixture's provisional ENU `(east,north,up)` to Three `(east,up,-north)` transform remains for that fixture only. Neither establishes general real-site coordinate or north/scale acceptance; Arnav/Alex review remains a shared gate.
- The forest, pine, ivory and lime palette follows the unmerged PR #4 design proposal provisionally. No exported prototype art or external font files are bundled.
- Orbit, zoom and pan use Three.js OrbitControls. Focusable camera buttons provide orbit, zoom and reset alternatives. The scene has a text description for screen readers.
