# CANOPY Sheffield · tree-planning workbench

**Event-day coordination:** [Team execution board, owners, Spark proof gates and presentation handoff](docs/EVENT_DAY_EXECUTION_2026-11-13.md). The 15:00 target / 16:00 latest engineering freeze is the team’s plan; the organiser’s actual cutoff takes precedence. [BUILD](docs/BUILD.md) remains the canonical engineering evidence record.

Compare where trees could provide additional shade, what a proposed layout costs, and which modelled constraints it satisfies.

## Why this exists

A tree that looks well placed in a 3D view might shade the wrong place, overlap shade already provided by a building, or exceed the planting budget. Comparing alternatives also means keeping the location, time period and assumptions consistent. CANOPY joins a numerical evaluator to an editable planning studio so a proposal can be inspected, changed and computed again—with the evidence kept alongside it.

The project is being developed for NVIDIA Hack for Impact Sheffield. **The runnable demonstration uses labelled synthetic geometry, not an accepted Sheffield site or a planting recommendation.**

## What works, and what remains

The integrated source contains:

- A React/Three.js studio with catalogue-position editing, accepted revisions, stale-result warnings and a review-pack download.
- A Python CPU evaluator for baseline versus proposed-tree shade, including static occluders, multiple trees, growth/leaf-state cases and supported winter limits.
- Finite-catalogue search with upfront costs in integer pence, overlap-aware marginal gains and a separate final-layout constraint checker. Results are best evaluated alternatives, not claimed global optima.
- Controlled relocation and scenario comparisons, with exact inputs, run IDs, units and source hashes.
- Immutable SQLite scenarios, asynchronous jobs, generated API types, rights-checked assets and current-selection/cache safeguards.
- A bounded local-model adapter and domain-tool loop. In a local development test (laptop/WSL, not the DGX Spark), a small Qwen model (not Nemotron) selected `evaluate_layout` and cited the stored run; tiny-model metadata completion still fails safely. Nemotron tool use on the DGX, reliable autonomous investigation and an AI advantage have **not** been established.

The full product is not finished. Real Sheffield geometry/rights/parity, target-model tool use on the DGX, complete autonomous planning, independent manual-versus-AI evaluation and full-system acceptance remain open. SSH access to the assigned DGX is verified. Ben reports ([#54](https://github.com/Pimentellll/sheffield-tree-planner/issues/54), team-reported) a loopback-only SSH preview of the CI-built release wheel (frontend built on the DGX) in which a browser click completed an evaluation on synthetic flat-ground geometry; it is a controlled baseline, not a deployment, and his hands-on acceptance is pending. A single Nemotron API smoke returned a response without a tool call. [BUILD](docs/BUILD.md) records issue-level evidence and the next gates; the #54 report is newer than BUILD's DGX entries.

### A concrete run

Launch the physical studio below, evaluate the initial placement, run a constrained search, then change a supported requirement and accept it. The old result becomes stale; the backend computes a new result for the accepted revision. The comparison and review-pack views expose the stored records rather than estimates written by the UI.

For a repeatable non-interactive check, run the installed `tree_planner.evaluators.physical_demo` module. It exercises real loopback HTTP, jobs, CPU evaluation, search and comparisons, writes the observed evidence, and shuts down its owned server. It does not need a model or a DGX.

## How it is built

- **Numerical tools own the numbers.** The model can request registered domain operations, but has no shell, arbitrary network or direct database tool.
- **Inputs and results have identities.** Accepted/hypothetical scenarios, immutable revisions, input fingerprints and selection slots prevent late or cached results being presented as current.
- **Feasibility is checked separately.** The search proposes layouts; a distinct validator checks the supported hard constraints. Unknown utilities, soil and permissions stay survey requirements.
- **Geometry and uncertainty are explicit.** The CPU runtime currently supports an authored, flat-ground scene/catalogue. It does not infer canopy semantics from a real-world mesh or equate shade with cooling, carbon, air quality or flood reduction.

The canonical product version is `0.2.0` in `pyproject.toml`, a minor expansion from the readiness-only `0.1.0`. It has not been tagged or published as a release. The frontend's private npm version is component metadata, not a second product version.

## Install and run

Requires Python 3.11+ (CI covers 3.11/3.12), Node.js 22.12+ and [uv](https://docs.astral.sh/uv/). From a checkout:

```text
uv sync --frozen --extra dev --python 3.11
npm ci --prefix frontend
```

**Windows PowerShell — terminal 1, repository root:**

```powershell
.venv/Scripts/python.exe frontend/scripts/serve_physical.py --workspace ../canopy-physical-01 --winter
```

**Windows PowerShell — terminal 2, repository root:**

```powershell
$env:CANOPY_SESSION = (Resolve-Path ../canopy-physical-01/session.json).Path
npm --prefix frontend run dev -- --host 127.0.0.1
```

**Linux — terminal 1, repository root:**

```bash
.venv/bin/python frontend/scripts/serve_physical.py --workspace ../canopy-physical-01 --winter
```

**Linux — terminal 2, repository root:**

```bash
CANOPY_SESSION="$(realpath ../canopy-physical-01/session.json)" npm --prefix frontend run dev -- --host 127.0.0.1
```

Open **http://127.0.0.1:5173**. The API uses loopback port 8765. Use a new workspace name for each fresh run; the launcher refuses to overwrite an existing workspace. Stop both terminals with Ctrl-C. This is a local demonstration, not a publicly authenticated service.

Run the numerical evidence path without the browser:

```text
uv run --frozen --no-sync python -m tree_planner.evaluators.physical_demo --output ../canopy-proof-01
```

For the separate pinned one-tree reference, failure/zero rehearsal and UI controls, see [frontend setup](frontend/README.md), [demo runbook](frontend/DEMO.md), [physical runtime](docs/PHYSICAL_RUNTIME.md) and [reference runtime](docs/REFERENCE_RUNTIME.md).

### Build an installable artifact

```text
uv build
```

The wheel packages the Python backend and readiness CLI. The source distribution additionally contains frontend source, its lockfile and launch scripts; it needs `npm ci` and a frontend build. Neither artifact includes model weights, restricted site assets or the external checkout used by the historical one-tree reference. Install the built wheel in a fresh environment and run `python -m tree_planner.evaluators.physical_demo` outside the source checkout for a real package smoke test.

### Tests

```text
uv run --frozen --no-sync python -m pytest -q -rs
uv run --frozen --no-sync ruff check src backend scripts tests ci
uv run --frozen --no-sync python scripts/generate_api_types.py --check
npm --prefix frontend run build
npm --prefix frontend test
```

The reference tests need the exact numerical checkout documented in [REFERENCE_RUNTIME](docs/REFERENCE_RUNTIME.md). Live-model tests are explicit opt-ins; skipped device/model tests are not passes. The frontend's `test:physical` and `test:browser` scripts run against real, fresh backend/UI sessions; follow its setup instructions rather than reusing a demo workspace.

[Readiness CI](.github/workflows/readiness.yml) checks Linux/Windows, generated contracts, built artifacts and installed smoke paths. [Frontend CI](.github/workflows/frontend.yml) checks the build, units and real browser integrations. Consult the checks on the exact commit: an older green branch does not verify a new one. PR checks do not deploy or download models. Tags, releases, DGX deployment and competition submission are separate operations.

## Team and next steps

- Ben — backend, integration and local-model tools: [bbeennyy860-cyber](https://github.com/bbeennyy860-cyber).
- Arnav — numerical and geospatial foundations: [reverez](https://github.com/reverez).
- Alex — planning studio and evidence UI: [akurkar07](https://github.com/akurkar07).

Start with [development documentation](docs/README.md) and the current [BUILD status](docs/BUILD.md). The [contracts](docs/CONTRACTS.md), [numerics](docs/NUMERICS.md) and [validation criteria](docs/VALIDATION.md) define meaning and evidence; the [feature catalogue](docs/FEATURE_PRIORITIES.md) distinguishes the MVP from later research.

Use scoped branches and isolated worktrees. Preserve source credit, advance-work provenance and existing teammates' branches. Never commit passwords, private keys, private prompts, raw restricted assets or generated runtime workspaces. Repository visibility is public; no open-source licence has been assigned. Confirm event eligibility and third-party asset/model permissions independently.

Canonical repository: https://github.com/Pimentellll/sheffield-tree-planner.
