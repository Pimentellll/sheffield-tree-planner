"""Serve the opt-in synthetic numerical runtime on loopback, with owned shutdown."""

import argparse
import json
from pathlib import Path
import socket
import sys
from threading import Thread

from fastapi.staticfiles import StaticFiles
import uvicorn

from .physical_runtime import create_physical_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--winter", action="store_true")
    parser.add_argument("--frontend-dist", type=Path)
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--cleanup-file", type=Path)
    parser.add_argument("--control-stdin", action="store_true")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("port must be between 0 and 65535")
    runtime = create_physical_runtime(args.workspace, winter=args.winter)
    if args.frontend_dist:
        front = args.frontend_dist.resolve(strict=True)
        if not (front / "index.html").is_file() or args.workspace.resolve().is_relative_to(front):
            parser.error("Built frontend required; private workspace must be outside it")
        runtime.app.mount("/", StaticFiles(directory=front, html=True, follow_symlink=False))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", args.port))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(runtime.app, log_level="warning", access_log=False))
    status = dict(
        url=base,
        scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
        ui_url=f"{base}/?scenario={runtime.scenario_ref.scenario_id}&revision=1",
        scope="Authored synthetic numerical case; no real-site/model/human acceptance",
    )
    if args.status_file:
        args.status_file.parent.mkdir(parents=True, exist_ok=True)
        args.status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
    if args.control_stdin:

        def control():
            for line in sys.stdin:
                try:
                    if json.loads(line) == {"action": "shutdown"}:
                        server.should_exit = True
                        return
                except ValueError:
                    continue

        Thread(target=control, daemon=True).start()
    print(json.dumps(status), flush=True)
    try:
        server.run(sockets=[sock])
    finally:
        sock.close()
        cleanup = dict(
            listener_closed=sock.fileno() == -1,
            worker_stopped=runtime.app.state.service.worker is None,
        )
        if args.cleanup_file:
            args.cleanup_file.write_text(json.dumps(cleanup, indent=2), encoding="utf-8")
        print(json.dumps(dict(cleanup=cleanup)), flush=True)


if __name__ == "__main__":
    main()
