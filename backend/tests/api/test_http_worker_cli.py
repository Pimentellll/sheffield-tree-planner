"""Real ownership and CLI checks; no successful numerical Results are constructed."""

from pathlib import Path
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from tree_planner.api import create_app
from tree_planner.api.__main__ import main
from tree_planner.api.service import WorkspaceLease
from tree_planner.site.repository import DomainError


def unavailable(*args):
    raise RuntimeError("intentionally unavailable synthetic test provider")


def test_lock_is_real_across_processes(tmp_path):
    lock = WorkspaceLease(tmp_path)
    code = """
import sys
from pathlib import Path
from tree_planner.api.service import WorkspaceLease
from tree_planner.site.repository import DomainError
lease = WorkspaceLease(Path(sys.argv[1]))
try:
    lease.acquire()
except DomainError:
    print('owned')
else:
    lease.release()
    print('free')
"""
    with lock.held():
        result = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, timeout=15
        )
        assert result.returncode == 0 and result.stdout.strip() == "owned", result.stderr
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0 and result.stdout.strip() == "free", result.stderr


def test_lifespan_owns_one_worker_and_refuses_second_recovery(tmp_path):
    app = create_app(tmp_path, handlers={"evaluate_layout": unavailable})
    second = create_app(tmp_path, handlers={"evaluate_layout": unavailable})
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/v1/health").json()["worker_mode"] == "background"
        assert app.state.worker is not None
        with pytest.raises(DomainError):
            with TestClient(second, base_url="http://127.0.0.1"):
                pass
        with pytest.raises(DomainError):
            second.state.run_one()
        with pytest.raises(DomainError):
            app.state.run_one()
    with TestClient(second, base_url="http://127.0.0.1") as client:
        assert client.get("/api/v1/health").json()["worker_mode"] == "background"


def test_no_provider_means_manual_and_no_recovery(tmp_path, monkeypatch):
    app = create_app(tmp_path)

    def forbidden(**kwargs):
        raise AssertionError("no recovery without an exclusive running worker")

    monkeypatch.setattr(app.state.jobs, "recover_exclusive_startup", forbidden)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/v1/health").json()["worker_mode"] == "manual"


def test_cli_exact_uvicorn_security_configuration(tmp_path, monkeypatch):
    calls = []
    import uvicorn

    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: calls.append((app, kwargs)))
    assert (
        main(
            ["--workspace", str(tmp_path), "--port", "8123", "--ui-origin", "http://localhost:5173"]
        )
        == 0
    )
    assert calls[0][1] == dict(
        host="127.0.0.1",
        port=8123,
        workers=1,
        proxy_headers=False,
        server_header=False,
        access_log=False,
    )
    assert calls[0][0].state.repository.workspace == Path(tmp_path)


@pytest.mark.parametrize(
    "args",
    [
        ["--host", "0.0.0.0"],
        ["--port", "0"],
        ["--port", "65536"],
        ["--ui-origin", "https://foreign.invalid"],
        ["--ui-origin", "http://127.0.0.1:5173/path"],
    ],
)
def test_cli_refuses_nonlocal_configuration(tmp_path, args):
    with pytest.raises(SystemExit) as exc:
        main(["--workspace", str(tmp_path), *args])
    assert exc.value.code == 2


@pytest.mark.parametrize("flag", ["--version", "--help"])
def test_real_module_cli(flag):
    result = subprocess.run(
        [sys.executable, "-m", "tree_planner.api", flag], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_trusted_handler_registry_is_not_callback_discovery(tmp_path):
    with pytest.raises(ValueError):
        create_app(tmp_path, handlers={"shell": unavailable})
    with pytest.raises(ValueError):
        create_app(tmp_path, handlers={"evaluate_layout": "https://untrusted.invalid/callback"})
