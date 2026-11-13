# CANOPY frontend: planning studio (STP-007 / STP-012 / STP-013)

React + Three.js planning studio wired to the real local backend (`backend/`, PR #45). It places one proposed tree, saves the move as a new immutable layout and accepted scenario revision, submits an `evaluate_layout` job, polls it, and shows the stored Result with its run identity, units, cost, provenance and currentness. The UI never computes or invents a metric: with no backend, no number is shown.

The only site the backend can evaluate today is Ben's **explicit synthetic one-tree reference** (receiver sample, chosen sun direction). It is labelled synthetic throughout; it is not Sheffield.

## Run locally

Requires Node.js 20.19+/22.12+, Python 3.11+, the repository installed into `.venv` (see the root README), and Arnav's numerical checkout at the commit pinned in `docs/REFERENCE_RUNTIME.md` (`33493a3…`, branch `spike/arnav/STP-010-mask-reference`) as a sibling directory `repo-numerical-inputs`.

```bash
# terminal 1, from the repository root: real API + worker + trusted synthetic evaluator on :8765
.venv/bin/python frontend/scripts/serve_reference.py --workspace ../canopy-dev-run --numerical-source ../repo-numerical-inputs

# terminal 2, from frontend/
npm ci
CANOPY_SESSION=../../canopy-dev-run/session.json npm run dev     # http://127.0.0.1:5173
```

PowerShell: use `.venv/Scripts/python.exe`, `npm.cmd`, and `$env:CANOPY_SESSION='..\..\canopy-dev-run\session.json'`. The workspace directory must not exist yet (the runtime never overwrites stored runs). `CANOPY_API` overrides the backend URL (default `http://127.0.0.1:8765`).

Without the launcher you can still open `?scenario=<id>&revision=<n>` against any running backend; geometry is then not drawn, because no verified declaration is supplied.

## Physical runtime (Ben's takeover-v1)

With Ben's `feat/ben/STP-arnav-logic-takeover` checkout (or later), start `python frontend/scripts/serve_physical.py --workspace <fresh> --winter` from that checkout's environment, then run the dev server with `CANOPY_SESSION=<fresh>/session.json`. The launcher calls `create_physical_runtime` unchanged, reads the scene asset through the registry's rights-checked `read(..., "public_display_status")`, and the UI verifies its SHA-256 before drawing the 195 receiver samples, planting region and catalogue positions. Because this backend evaluates catalogue candidates only, the editor becomes a candidate picker: drags snap to positions and the arrow keys step between them. Search, winter cases, `compare_locations` and `compare_scenarios` then show real results. `npm run test:physical` checks all of this against the live server (19 checks).

## Real terrain context (view only)

The Sheffield sites screen can show real Environment Agency LiDAR as a navigable 3D surface. It is a context view: it is not a SiteBundle, is not sent to the backend, and no shade result refers to it.

1. Download tile **SK38NW** from https://environment.data.gov.uk/survey: *LIDAR Composite DTM* and *LIDAR Composite First Return DSM*, 2022, 1 m. Keep the two .zip files out of git.
2. `uv run --with rasterio --with numpy python frontend/scripts/prepare_terrain.py --dtm <DTM zip> --dsm <DSM zip> --out ../canopy-terrain` crops Weston Park plus the 450 m context buffer from the STP-005 audit, and records file hashes, survey, licence and attribution.
3. Start the dev server with `CANOPY_TERRAIN_DIR=../../canopy-terrain`.

Heights are drawn as stored, with no vertical exaggeration. Colours are bands of height above ground; a surface model cannot tell buildings from canopy, and the legend says so. `npm run test:terrain` checks labelling and navigation (`CANOPY_TERRAIN_EXPECT=absent|synthetic|real`); `scripts/make_test_terrain.py` writes a labelled synthetic surface for that check.

## Tests

- `npm test`: Vitest unit tests for the stale-result rules, commit/revision building, job states, formatting, API client (If-Match, ContractError, head probing, cancel), declaration hash verification and the ENU→viewer transform.
- `npm run build`: strict TypeScript + production bundle.
- `npm run test:browser`: integrated check in a real browser against the running backend and dev server (set `CANOPY_BROWSER` if Chrome/Edge isn't in a standard place). Start from a **fresh** launcher workspace. It asserts the backend's 2 m²·h positive result, immediate staleness on an unsaved edit, the 0 m²·h valid zero after saving a move, the older revision shown as superseded, keyboard editing, and a narrow 390 px layout. With `CANOPY_DEV_WORKSPACE=<launcher workspace>` it also corrupts (then restores) only the launcher's generated asset to prove the change fails closed with no new number. `CANOPY_OFFLINE=1` checks the not-connected state instead. Screenshots and a JSON receipt go to the ignored `artifacts/`.

## How currentness works

A stored Result is shown as **CURRENT** only if it was computed for the head accepted scenario revision, the backend's `selections(...).evaluation.current_job` is that run, and the draft has no unsaved move. Otherwise it is labelled **STALE · UNSAVED EDITS** (number struck through), **NOT CURRENT** (the backend selected another run, or a later failure cleared the selection) or **SUPERSEDED** (older revision). A job that finishes after a newer revision exists can only enter history. Results whose `source_job_id`/`input_fingerprint` don't match their job are refused.

Saving a move registers layout revision *n+1* and replaces the scenario with `If-Match`. If the scenario's job deadline (`search.deadline_utc`, which bounds job admission) is within 10 minutes of expiry, the same save renews it to two hours ahead and says so.

## Geometry and frame

- Drawn geometry comes only from the backend: the layout placement, the profile state (crown ellipsoid radii and centre height, trunk radius and height) and the synthetic declaration. The declaration bytes are checked against the SiteBundle asset SHA-256 before anything is drawn.
- The receiver is drawn as a disc of its *represented* area (2 m²); it is a sample, not a surveyed polygon. The dashed line is the declared sun direction the evaluator uses, an input shown for orientation, not a result. There is no sun-time slider, so nothing view-only appears to change the analysis.
- Viewer transform: ENU (east, north, up) → Three (east, up, −north), row-major `[1,0,0,0, 0,0,1,0, 0,−1,0,0, 0,0,0,1]`, matching Arnav's STP-006 known points. Ben's synthetic SiteBundle sends an **identity** `analysis_to_viewer`; the UI reports that mismatch on screen and in an issue instead of silently reinterpreting it.
- Editing: drag the tree on the ground plane, or focus the view and use the arrow keys (0.1 m, Shift 1 m; up = north), or type East/North. Positions are stored to the millimetre and limited to ±50 m. "Find tree" recentres the camera.

## Known limits

- Live cancellation is implemented and unit-tested, but the reference evaluator finishes in tens of milliseconds, so it has not been exercised against a running job.
- With the reference backend, a changed source asset is refused at admission as `REVISION_CONFLICT` (409), not as a failed job. The UI shows the backend's code and message and does not guess the cause. The failed-job path is covered by unit tests only.
- Search, comparison, multi-tree, seasons and the agent panel are later STP items (018, 021, 025).
