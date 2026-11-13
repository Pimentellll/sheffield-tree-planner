"""Serve Ben's synthetic reference runtime for frontend development (STP-013).

Starts the real CANOPY API with the trusted one-tree evaluator from
`tree_planner.evaluators.runtime.create_reference_runtime` and writes a session file
that the Vite dev server exposes to the browser. No backend code is modified and no
result is fabricated: every number the UI shows comes from this server's jobs.

    python frontend/scripts/serve_reference.py \
        --workspace ../canopy-dev-run --numerical-source ../repo-numerical-inputs

The workspace must not already exist. The numerical source is Arnav's checkout at the
commit pinned in docs/REFERENCE_RUNTIME.md.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path

NUMERICAL_COMMIT = "33493a327a99e5de2e579b5c3070ada137047c7e"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, required=True, help="fresh local directory")
    parser.add_argument(
        "--numerical-source", type=Path, default=os.environ.get("CANOPY_NUMERICS_SOURCE")
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--session",
        type=Path,
        default=None,
        help="session JSON for the Vite dev server (default: <workspace>/session.json)",
    )
    args = parser.parse_args(argv)
    if args.numerical_source is None:
        parser.error("--numerical-source or CANOPY_NUMERICS_SOURCE is required")

    import uvicorn
    from tree_planner.evaluators.runtime import create_reference_runtime

    workspace = args.workspace.resolve()
    runtime = create_reference_runtime(workspace / "runtime", numerical_source=args.numerical_source)
    site = runtime.app.state.service.scenarios.get_site(
        "synthetic-reference", 1, 1
    )
    asset = site.assets[0]
    declaration = (workspace / "runtime" / "inputs" / "synthetic-reference.json").read_bytes()
    session = dict(
        kind="canopy-dev-session",
        label="Synthetic reference runtime (trusted one-tree evaluator; not Sheffield)",
        scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
        declaration_asset_id=asset.asset_id,
        declaration_b64=base64.b64encode(declaration).decode("ascii"),
        numerical_source_commit=NUMERICAL_COMMIT,
        started_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    session_path = (args.session or workspace / "session.json").resolve()
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    print(f"CANOPY reference API on http://127.0.0.1:{args.port}", flush=True)
    print(f"Session file: {session_path}", flush=True)
    print(f"Scenario: {runtime.scenario_ref.scenario_id} revision {runtime.scenario_ref.revision}", flush=True)
    uvicorn.run(
        runtime.app,
        host="127.0.0.1",
        port=args.port,
        workers=1,
        proxy_headers=False,
        server_header=False,
        access_log=False,
        log_level="warning",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
