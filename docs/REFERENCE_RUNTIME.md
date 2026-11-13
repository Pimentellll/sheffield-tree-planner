# Synthetic reference runtime

`tree_planner.evaluators.runtime.create_reference_runtime` creates a fresh local
workspace, verifies the approved `shade_reference.py` and `ray.py` bytes in the
separately supplied numerical checkout, and loads those exact bytes without
executing that checkout's package initializers or using cached bytecode. It does
not copy or modify the producer source. Changed or missing producer/provider
source fails closed; restart is required after provider edits.

The factory registers a generated input asset, explicit synthetic rights evidence,
typed SiteBundle, profile, layout and accepted scenario through actual services.
`SyntheticScene` contains immutable finite receiver geometry/area, chosen analytic
sun direction, UTC bin and baseline ellipsoids. Its asset bytes and exact site
binding are checked at runtime. The one tree derives from the admitted profile
and placement. These are synthetic declarations, not surveyed site geometry or
a SiteBundle geometry importer. The geographic fields are unused placeholders.
The chosen sun is due south at 45 degrees elevation by default; its timestamp
labels an integration bin. No SPA or geographic solar-position computation runs.

`ReferenceJobHandler.execution_hashes(dependencies, *, operation)` hashes the
resolved numerical dataclasses, full dependency binding, actual source/code and
configuration. It never calls application resolution. The provider resolves via
`ApplicationService.resolve_for_execution`, which adds `execution:` hashes to
authoritative admission identity. The handler checks that identity before and
after calculation and checks the actual inputs passed to the calculator.
Explicit `synthetic_stub=True` providers are for boundary tests: code and resolved
inputs are hashed, but closure/global integrity and trusted producer loading are
not proved. The factory uses verified source loading, not that stub mode.

After installing into `.venv` as described in README, provide a separate numerical
checkout at commit `33493a327a99e5de2e579b5c3070ada137047c7e`. The example assumes
that checkout is the sibling `repo-numerical-inputs`; change only that path to
match your checkout. The installed CLI needs no source-tree `PYTHONPATH`.

From this repository in PowerShell:

```powershell
$numericalSource = (Resolve-Path '../repo-numerical-inputs').Path
& '.venv/Scripts/python.exe' -m tree_planner.evaluators.demo `
    --output '../reference-proof-new' `
    --numerical-source $numericalSource
```

The output directory must be fresh. The demo binds an ephemeral loopback TCP
port and starts Uvicorn plus a real background worker. It submits/polls HTTP
jobs and reads stored Results/current selection. It asserts the actual positive
2 m²·h calculation, an actual missed-tree zero after a geometry/scenario revision,
stale selection and immutable old results. It stops its worker to admit a job,
corrupts only its generated asset, resumes execution and observes a real failed
job without a Result, then restores the exact bytes and computes recovery. JSON
evidence retains actual HTTP responses, hashes, runs, invariants and shutdown
checks. Failure exits nonzero. All owned server/worker threads stop on completion.

Only `evaluate_layout` is available. Feasibility stays `not_evaluated`; constraints
stay unknown. No search, model, frontend, real Sheffield, science acceptance or
deployment is proved. This is trusted single-process startup, not protection
against hostile code already executing inside the server process.
