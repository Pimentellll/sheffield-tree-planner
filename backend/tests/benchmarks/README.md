# B11 runner adapter contract

Run with the exact project Python:

```powershell
.venv/Scripts/python.exe backend/tests/benchmarks/runner.py --tasks <held-out-manifest.json> --output <new-output-dir> --adapter <module:factory>
```

The adapter is local experiment glue, not benchmark evidence. Its factory signature is `factory(task, mode_workspace, mode) -> environment`. Each environment supplies:

- `dispatcher`: the real task-pinned backend `AgentDispatcher` (the runner wraps and records its actual returned jobs/results);
- `comparison_identity()`: `input_fingerprint`, `data_sha256`, `tools_sha256`, and `backend_config_sha256`, identical across all three fresh mode runtimes;
- `run(mode, task, recording_dispatcher) -> observation`;
- optional `metadata(mode) -> safe config metadata`, including exact requested inference route/model and exposed native session IDs when adaptive execution is attempted. Report attestation as unavailable unless the provider actually exposes it.

Observation fields are `user_actions` (timestamped, with scripted/human origin), `numeric_claim_audits` and `claim_audit_complete` (independent scorer only), `useful_analysis_run_ids` (scorer-selected result IDs), and `tool_errors`. Operation events, job/result receipts, constraint checks and elapsed time are replaced/derived by the harness from actual dispatcher/backend observations. The runner keeps failed runs. Task fixtures and computed evidence must be synthetic-labelled. Scripted manual-mode input must remain labelled scripted.

`physical_adapter:physical_factory` supplies a deterministic scripted fixed workflow against `create_physical_runtime` and the actual `AgentDispatcher`; this is reported as scripted, not a human run. It uses the same accepted synthetic scenario, scene, operation schemas, numeric/search settings and backend source/dependency manifest per ordinary task. The failure task applies a labelled byte change to its fresh synthetic registered scene to exercise the actual source-integrity failure path; no old result is supplied. Random scenario/job/source identifiers, the source-derived candidate fingerprint, and seed-time deadline are excluded from the normalized configuration identity and documented in each receipt. The manual arm is blocked because no captured UI/action adapter is available. The adaptive arm is blocked because the prior authorized loopback check to `http://127.0.0.1:8001/v1` timed out; no model call, provider startup, or configuration occurs here. Neither blocked arm is written as a failed run.

The task pack includes synthetic counterfactual and feasibility/search strata. Actual execution must wait for the physical runtime and search source to be frozen and imported. A reachable authorized loopback model provider is separately required for a genuine adaptive run; the runner never starts or configures one.
