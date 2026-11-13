# CANOPY · Tree-planning workbench

Explore where trees could add shade, compare planting layouts and inspect the evidence behind each result.

**The runnable demo uses an authored synthetic site. It is not a surveyed Sheffield site or a planting recommendation.**

![CANOPY Studio showing a synthetic planting layout, computed shade and a disconnected planning agent](docs/images/studio.png)

*Actual synthetic-demo capture from [frontend CI](https://github.com/Pimentellll/sheffield-tree-planner/actions/runs/43451276964), commit `5b2dbd43`. The model is not connected in this run.*

## Why this exists

A tree can look well placed on a map while shading the wrong area, duplicating a building's existing shade or exceeding the planting budget. Comparing alternatives also means holding the site, time period and assumptions consistent. CANOPY brings those decisions into an editable 3D workbench, with numerical results you can trace back to their inputs.

## What you can do

- Inspect the site and proposed trees in the **Studio**.
- Edit catalogue positions, budget and supported requirements; accept a revision and recompute it.
- Search a finite catalogue for planting alternatives under the configured constraints.
- Compare stored runs, shade metrics, costs and supported winter-sun trade-offs.
- Inspect assumptions, unknown constraints and provenance, then download a browser-built review pack.

Try this: evaluate a layout, edit its budget, then accept the change. The previous result becomes stale until the backend produces a result for the new revision. The UI reads stored results; it does not estimate the answer itself.

### Current scope

The working baseline is the **manual, local CPU planning workflow**. The repository also contains local-model client, tool-loop and evidence-presentation code, but the main interface does not yet provide a connected planning agent. End-to-end Nemotron tool use on the DGX is not established.

The current evaluator uses an authored flat-ground scene. Geospatial import utilities and recorded-tree inventory tooling are not proof of a validated real-site workflow. Shade is not presented as measured cooling, carbon reduction, flood mitigation or energy-bill savings. Search results are evaluated alternatives, not claimed global optima.

## How it is built

```text
React / Three.js studio
        ↓
Local FastAPI backend → durable jobs → CPU geometry and search
        ↓
Immutable scenarios, stored results and provenance
```

The numerical tools own the calculations. Scenario revisions and result identities keep stale, cached and superseded runs distinguishable. Search proposes layouts; a separate checker evaluates the supported constraints. Unknown site conditions remain unknown.

- `frontend/` — interface, scene renderer and browser checks.
- `backend/src/tree_planner/` — contracts, local API, storage, jobs, physics, search and agent loop.
- `backend/tests/` and `tests/` — regression, protocol and integration checks.
- `docs/` — product scope, technical contracts, runbooks and engineering evidence.

Start with the [documentation index](docs/README.md). Detailed state and ownership belong in [BUILD](docs/BUILD.md), not in this README.

## Run the local demo

Requires **Python 3.11+**, **Node.js 22.12+** and [uv](https://docs.astral.sh/uv/). The manual demo needs neither model weights nor a cloud-model account.

From the repository root:

```text
uv sync --frozen --extra dev --python 3.11
npm ci --prefix frontend
```

<details open>
<summary>Windows PowerShell</summary>

Terminal 1, repository root:

```powershell
.venv/Scripts/python.exe frontend/scripts/serve_physical.py --workspace ../canopy-physical-01 --winter
```

Terminal 2, repository root:

```powershell
$env:CANOPY_SESSION = (Resolve-Path ../canopy-physical-01/session.json).Path
npm --prefix frontend run dev -- --host 127.0.0.1
```

</details>

<details>
<summary>Linux</summary>

Terminal 1, repository root:

```bash
.venv/bin/python frontend/scripts/serve_physical.py --workspace ../canopy-physical-01 --winter
```

Terminal 2, repository root:

```bash
CANOPY_SESSION="$(realpath ../canopy-physical-01/session.json)" npm --prefix frontend run dev -- --host 127.0.0.1
```

</details>

Open **http://127.0.0.1:5173**. The backend uses port **8765**. Use a fresh workspace name for each new demo; existing workspaces are not overwritten. Stop both terminals with Ctrl-C. Keep the services on loopback: this is not a public, multi-user authenticated deployment.

### Tests and packaging

```text
uv run --frozen --no-sync python -m pytest -q -rs
uv run --frozen --no-sync ruff check src backend scripts tests ci
uv run --frozen --no-sync python scripts/generate_api_types.py --check
npm --prefix frontend run build
npm --prefix frontend test
uv build
```

Some reference checks require the [pinned numerical source](docs/REFERENCE_RUNTIME.md); live-model checks require explicit opt-in. A skipped model test is not model proof. [Frontend setup](frontend/README.md) covers fresh-session browser checks; [physical runtime](docs/PHYSICAL_RUNTIME.md) covers the numerical demo and non-interactive evidence path.

The wheel contains the Python backend and readiness CLI. The source distribution also includes frontend source and its lockfile; the frontend still needs installation and a build. Neither includes model weights or restricted site assets. [Backend CI](.github/workflows/readiness.yml) and [frontend CI](.github/workflows/frontend.yml) verify source and artifacts, but do not deploy them to the DGX.

## Project

Built by Ben, Arnav and Alex for NVIDIA Hack for Impact Sheffield. See the [feature catalogue](docs/FEATURE_PRIORITIES.md) for planned work and [validation criteria](docs/VALIDATION.md) for what counts as evidence.

Repository: [Pimentellll/sheffield-tree-planner](https://github.com/Pimentellll/sheffield-tree-planner). No open-source licence has been assigned; public visibility alone does not grant reuse rights. Do not commit credentials, private prompts, restricted assets or generated runtime workspaces.
