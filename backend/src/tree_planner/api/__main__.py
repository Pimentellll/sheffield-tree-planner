"""Run the local CANOPY server. Provider registration is trusted Python wiring."""

import argparse
from pathlib import Path

from .app import application_version, create_app
from .security import _origin


def _port(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= parsed <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return parsed


def _ui_origin(value):
    try:
        return _origin(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("UI origin must be an explicit loopback origin") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="CANOPY local server (local origin protection, not OS authentication)"
    )
    parser.add_argument("--version", action="version", version=application_version())
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--port", type=_port, default=8000)
    parser.add_argument(
        "--ui-origin",
        type=_ui_origin,
        action="append",
        default=[],
        help="explicit allowed loopback browser origin; repeatable",
    )
    args = parser.parse_args(argv)
    app = create_app(args.workspace, allowed_ui_origins=tuple(args.ui_origin))
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        workers=1,
        proxy_headers=False,
        server_header=False,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
