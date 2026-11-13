"""Serve Ben's synthetic physical runtime (takeover-v1) for frontend development.

Calls `tree_planner.evaluators.physical_runtime.create_physical_runtime` unchanged and
writes a session file with the exact registered scene asset bytes, so the UI can verify
them against the SiteBundle SHA-256 before drawing. Every number shown comes from this
server's jobs.

    python frontend/scripts/serve_physical.py --workspace ../canopy-physical-run --winter

Requires a checkout that contains the physical runtime (Ben's STP-arnav-logic-takeover
branch or later). The workspace must not already exist. For the single-origin built UI
(and Spark), use `python -m tree_planner.evaluators.physical_server --frontend-dist`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, required=True, help="fresh local directory")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--winter", action="store_true", help="add the leaf-off winter case")
    parser.add_argument("--session", type=Path, default=None)
    from tree_planner.agents.runs import add_cli_arguments, install

    add_cli_arguments(parser)
    args = parser.parse_args(argv)

    import uvicorn
    from tree_planner.evaluators.physical_runtime import create_physical_runtime
    from tree_planner.evaluators.physical_session import build_session

    workspace = args.workspace.resolve()
    if workspace.exists():
        parser.error(f"workspace {workspace} already exists; use a fresh path")
    workspace.mkdir(parents=True)
    runtime = create_physical_runtime(workspace / "runtime", winter=args.winter)
    ref = runtime.scenario_ref
    session = build_session(runtime)
    session_path = (args.session or workspace / "session.json").resolve()
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    print(f"CANOPY physical API on http://127.0.0.1:{args.port}", flush=True)
    print(f"Session file: {session_path}", flush=True)
    print(f"Scenario: {ref.scenario_id} revision {ref.revision}", flush=True)
    agent = install(runtime.app, f"http://127.0.0.1:{args.port}/api/v1", args)
    print(
        f"Planning agent: {agent.model if agent else 'not configured (manual workflow only)'}",
        flush=True,
    )
    uvicorn.run(runtime.app, host="127.0.0.1", port=args.port, workers=1, proxy_headers=False,
                server_header=False, access_log=False, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
