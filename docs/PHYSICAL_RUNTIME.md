# Local synthetic numerical runtime

This opt-in runtime is in the same **unreleased 0.2.0** feature train. It uses authored synthetic geometry at a declared latitude and actual pvlib SPA directions. No surveyed Sheffield geometry, biological forecast, human acceptance, model advantage or Spark execution is established.

From this checkout, using its Python 3.11 environment:

```powershell
uv sync --frozen --extra dev --python .venv/Scripts/python.exe
.venv/Scripts/python.exe -m tree_planner.evaluators.physical_demo --output .local/proof-001
.venv/Scripts/python.exe -m tree_planner.evaluators.physical_server --workspace .local/session-001 --winter --port 8000
```

Use fresh paths. The demo performs real loopback TCP HTTP → durable jobs → CPU computation for evaluation, search, relocation and both scenario-comparison modes. It captures actual inputs, jobs, Results, metric IDs, hashes, errors, timings and owned-port cleanup in `evidence.json`. The server prints the exact scenario reference and UI URL. Stop the interactive server with Ctrl+C. It never contacts a model or remote numerical service.

Installable replay, outside a source tree:

```powershell
uv build
uv venv --python 3.11 .local/wheel-env
uv pip install --python .local/wheel-env/Scripts/python.exe dist/sheffield_tree_planner_readiness-0.2.0-py3-none-any.whl
.local/wheel-env/Scripts/python.exe -I -m tree_planner.evaluators.physical_demo --output .local/wheel-proof-001
```

For a dependency-frozen installation, use the repository `uv.lock`/exported requirements with hashes. The wheel packages the numerical code; the historical one-tree reference remains available with its separately pinned source dependency. Old SQLite runs without the new integrity receipt are rejected rather than retroactively certified. Recompute in a fresh workspace.

The default API still registers no numerical handlers. This runtime explicitly registers `evaluate_layout`, `search_layouts`, `compare_locations` and `compare_scenarios`; health advertises those operations. The typed dispatcher, rights checks, accepted/hypothetical scopes, deadlines, cancellation, current selections and cache fences remain authoritative. A hypothetical comparison never accepts a scenario. Full-result caches require exact admission identity and a fresh trusted dependency check; geometry-mask reuse has its own compatibility key. Stored Results are protected by an independently stored digest, in addition to nested semantic checks. This protects integrity errors, not a hostile OS user who can rewrite both database records.

The internal producer seam is versioned **`canopy-physical-scene/1` / `takeover-v1`**. It consumes registered asset bytes, typed SiteBundle/Scenario/Layout/Profile snapshots, explicit ENU receiver samples and static triangles. The first supported planting terrain is declared flat ground; nonflat terrain fails closed. Read [physics producer notes](../backend/src/tree_planner/physics/README.md) for exact fields, numerical conventions, references and retained Arnav source credit. The synthetic terrain importer can produce meshes and this scene format only when its supported flat-ground/semantic conditions hold. It is not a general real-site importer.

Schema 0.1.0 has a compatible capability extension: `fixed_crossing` requires an explicit transmission in [0,1]; opaque serialization remains exactly `{mode:"opaque"}`. Named winter cases and limits resolve case/target identities. The old limited evaluator still rejects modes/cases outside its capability. Path-length foliage and weather/thermal/energy metrics remain unsupported. Regenerate consumers with `scripts/generate_api_types.py`.

Draft objective policy is explicit: `maximise_shade_under_budget` ranks the declared weighted utility, while every run retains unweighted physical additional shade. `minimise_cost_for_target` tests the **physical** primary-case threshold and seeks a lower cost evaluated solution. Search uses overlap-aware additions and local changes plus a distinct deterministic reference, with a separate full-layout final checker. It reports best evaluated layouts and does not claim a global optimum or an exact infeasibility proof. Unknown surveys remain unknown. Costs are integer upfront pence; this runtime rejects budgets/cost scopes beyond the exact numeric evidence range. Tiny exhaustive tests are validation baselines.

Relocation preserves tree identity, profiles, other placements and all scenario inputs. A known candidate moved away from its catalogue coordinate is computed only in explicit diagnostic mode; its failed feasibility remains visible. Scenario comparisons bind both immutable input graphs. Fixed-layout mode preserves placements; redesign reruns search under each declared scenario. Changes are enumerated, each side has its own case/constraint context, and deltas cite exact metric instances with matching units, quantity, horizon and target. Incompatible metric meanings receive no delta.

Alex's latest PR50 consumer was inspected and tested in an isolated copy. A trusted built frontend can optionally be served with `physical_server --frontend-dist <built-directory>` and the printed `?scenario=...` URL. This does not supply the legacy one-point geometry declaration: the UI must retain its missing/unverified geometry label. Metrics and evidence use the API. Rendering is not numerical or human acceptance evidence.

For affected checks use the exact environment and a profile-owned scratch directory:

```powershell
.venv/Scripts/python.exe -m pytest backend/tests/physics backend/tests/search backend/tests/evaluators/test_physical_runtime.py --basetemp=.local/check-001 -q
.venv/Scripts/python.exe scripts/generate_api_types.py --check
.venv/Scripts/python.exe -m ruff check backend/src backend/tests
uv lock --check
```

Real sites require verified source CRS/datum/transform controls, lawful asset rights, canopy semantics, context, survey and human review. The site receipt rejects the named Sheffield candidates until those gates have evidence. The B11 harness separates scripted fixed workflows from missing human/manual and genuine-model arms; provider absence is a blocker, not a successful adaptive run. Canonical task state and exact verification receipts belong in BUILD.
