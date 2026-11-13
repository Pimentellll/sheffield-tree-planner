"""Single-origin local browser harness for actual synthetic numerical computation.

This adds no default production API route, arbitrary asset download or successful
result fixture. The trusted bootstrap is inputs only, resolved against the same
active accepted scenario and source checks used for calculation admission.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys
from threading import Thread
from uuid import uuid4

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from tree_planner.contracts import M2Scene, M2Session
from tree_planner.site.repository import DomainError
from .runtime import create_reference_runtime


def create_ui_app(workspace: Path, *, numerical_source: Path, frontend_dist: Path) -> FastAPI:
    """Serve a trusted built UI beside the real API, never the private workspace."""
    front = Path(frontend_dist).resolve(strict=True)
    if not front.is_dir() or not (front / "index.html").is_file():
        raise ValueError("built frontend index.html is required")
    private = Path(workspace).resolve()
    if private == front or private.is_relative_to(front):
        raise ValueError("private workspace cannot be under the public frontend")
    runtime = create_reference_runtime(private, numerical_source=numerical_source)
    app = runtime.app
    app.state.m2_runtime = runtime
    session_id = uuid4().hex

    @app.get("/m2/session", response_model=M2Session)
    def session():
        service = app.state.service
        ref = service.jobs.active_ref()
        if ref is None or ref.scope != "accepted":
            raise DomainError("TOOL_UNAVAILABLE", "No accepted reference is active")
        # Read-only source integrity and provider checks precede every trusted view.
        deps, _ = service.resolve_for_execution(ref, operation="evaluate_layout")
        profile_id = deps["layout"]["placements"][0]["profile_id"]
        return M2Session.model_validate(
            {
                "mode": "synthetic_one_tree_reference",
                "session_id": session_id,
                "source_asset_sha256": deps["site"]["assets"][0]["sha256"],
                "scene": M2Scene.model_validate(runtime.scene.declaration()),
                "scenario": deps["scenario"],
                "site": deps["site"],
                "layout": deps["layout"],
                "profile": deps["profiles"][profile_id],
            }
        )

    # Only the caller-selected production build is public, not DB/input directories.
    app.mount("/", StaticFiles(directory=front, html=True, follow_symlink=False), name="m2-ui")
    return app


def main(argv: list[str] | None = None) -> int:
    """Run the local synthetic browser/API process with explicit owned shutdown."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True, help="Fresh private runtime path")
    parser.add_argument("--numerical-source", type=Path, required=True)
    parser.add_argument("--frontend-dist", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0, help="Loopback port; 0 selects a free port")
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--cleanup-file", type=Path)
    parser.add_argument(
        "--control-stdin", action="store_true", help="Owned test controller may send shutdown JSON"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    app = create_ui_app(
        args.workspace, numerical_source=args.numerical_source, frontend_dist=args.frontend_dist
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", args.port))
    url = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(app, log_config=None, log_level="info"))

    def control():
        for line in sys.stdin:
            try:
                command = json.loads(line)
            except ValueError:
                continue
            if command == {"action": "shutdown"}:
                server.should_exit = True
                return

    if args.control_stdin:
        Thread(target=control, name="owned-m2-shutdown", daemon=True).start()
    status = {
        "url": url,
        "scope": "synthetic one-tree local UI; no real site or planner acceptance",
    }
    if args.status_file:
        args.status_file.parent.mkdir(parents=True, exist_ok=True)
        args.status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status), flush=True)
    try:
        server.run(sockets=[sock])
    finally:
        sock.close()
        cleanup = {
            "owned_listener_closed": sock.fileno() == -1,
            "owned_worker_stopped": app.state.service.worker is None,
        }
        if args.cleanup_file:
            args.cleanup_file.parent.mkdir(parents=True, exist_ok=True)
            args.cleanup_file.write_text(json.dumps(cleanup, indent=2), encoding="utf-8")
        print(json.dumps({"cleanup": cleanup}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
