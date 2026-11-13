"""Cold CLI process must actually calculate, then stop its own worker/listener."""

import json
from pathlib import Path
import socket
import subprocess
import sys
from time import monotonic, sleep

import httpx


def test_cold_standalone_server_calculates_and_shuts_down(tmp_path):
    status, cleanup = tmp_path / "status.json", tmp_path / "cleanup.json"
    command = [
        sys.executable,
        "-m",
        "tree_planner.evaluators.physical_server",
        "--workspace",
        str(tmp_path / "runtime"),
        "--winter",
        "--port",
        "0",
        "--status-file",
        str(status),
        "--cleanup-file",
        str(cleanup),
        "--control-stdin",
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).resolve().parents[3],
    )
    base = None
    try:
        deadline = monotonic() + 45
        while not status.exists():
            assert process.poll() is None, "Owned server exited before startup"
            assert monotonic() < deadline, "Cold startup did not become ready"
            sleep(0.05)
        info = json.loads(status.read_text())
        base = info["url"]
        with httpx.Client(
            base_url=base, headers={"Origin": base}, timeout=10, trust_env=False
        ) as client:
            while True:
                try:
                    if client.get("/api/v1/health").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                assert monotonic() < deadline
                sleep(0.05)
            response = client.post(
                "/api/v1/jobs",
                json=dict(
                    request_id="cold-start",
                    scenario_ref=info["scenario_ref"],
                    operation="evaluate_layout",
                    arguments=dict(layout_ref=dict(layout_id="one-tree", revision=1)),
                ),
            )
            assert response.status_code == 202, response.text
            job = response.json()
            deadline = monotonic() + 20
            while job["status"] not in {"completed", "failed", "cancelled"}:
                assert monotonic() < deadline, "Cold CLI numerical operation did not finish"
                sleep(0.05)
                job = client.get("/api/v1/jobs/" + job["job_id"]).json()
            assert job["status"] == "completed", job
            result = client.get("/api/v1/results/" + job["run_id"]).json()
            assert any(
                m["metric_id"] == "additional_shade" and m["value"] > 0 for m in result["metrics"]
            )
    finally:
        if process.poll() is None:
            process.stdin.write('{"action":"shutdown"}\n')
            process.stdin.flush()
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.communicate(timeout=10)
            raise
    assert process.returncode == 0, (stdout, stderr)
    assert all(json.loads(cleanup.read_text()).values())
    with socket.socket() as probe:
        assert probe.connect_ex(("127.0.0.1", int(base.rsplit(":", 1)[1]))) != 0
