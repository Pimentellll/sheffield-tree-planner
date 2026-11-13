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

No adapter is currently supplied. Do not use scripted outputs as human/model evidence. The task pack includes counterfactual/search strata that the current pre-takeover branch did not implement; root's agreed physical runtime/API seams are a dependency for actual execution. The adaptive arm additionally requires an already-running authorized loopback model provider; the runner neither starts nor configures one.
