"""Serve Ben's synthetic physical runtime (takeover-v1) for frontend development.

Calls `tree_planner.evaluators.physical_runtime.create_physical_runtime` unchanged and
writes a session file with the exact registered scene asset bytes, so the UI can verify
them against the SiteBundle SHA-256 before drawing. Every number shown comes from this
server's jobs.

    python frontend/scripts/serve_physical.py --workspace ../canopy-physical-run --winter

Requires a checkout that contains the physical runtime (Ben's STP-arnav-logic-takeover
branch or later). The workspace must not already exist.
"""

from __future__ import annotations

import argparse
import base64
import json
from datetime import datetime, timezone
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, required=True, help="fresh local directory")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--winter", action="store_true", help="add the leaf-off winter case")
    parser.add_argument("--session", type=Path, default=None)
    args = parser.parse_args(argv)

    import uvicorn
    from tree_planner.evaluators.physical_runtime import create_physical_runtime

    workspace = args.workspace.resolve()
    if workspace.exists():
        parser.error(f"workspace {workspace} already exists; use a fresh path")
    workspace.mkdir(parents=True)
    runtime = create_physical_runtime(workspace / "runtime", winter=args.winter)
    service = runtime.app.state.service
    ref = runtime.scenario_ref
    scenario = service.scenarios.get_scenario(ref)
    inp = scenario.input
    site = service.scenarios.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
    asset = next(a for a in site.assets if a.kind == "canopy_physical_scene_v1")
    # Rights-checked read: refused unless the source permits public display.
    scene_bytes = service.assets.read(asset.ref.registry_id, "public_display_status")
    session = dict(
        kind="canopy-dev-session",
        label="Synthetic physical runtime takeover-v1 (authored geometry; not Sheffield)",
        scenario_ref=ref.model_dump(mode="json"),
        declaration_asset_id=asset.asset_id,
        declaration_b64=base64.b64encode(scene_bytes).decode("ascii"),
        numerical_source_commit="physical runtime (no external numerical source)",
        started_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    session_path = (args.session or workspace / "session.json").resolve()
    session_path.write_text(json.dumps(session, indent=2), encoding="utf-8")
    print(f"CANOPY physical API on http://127.0.0.1:{args.port}", flush=True)
    print(f"Session file: {session_path}", flush=True)
    print(f"Scenario: {ref.scenario_id} revision {ref.revision}", flush=True)
    uvicorn.run(runtime.app, host="127.0.0.1", port=args.port, workers=1, proxy_headers=False,
                server_header=False, access_log=False, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
