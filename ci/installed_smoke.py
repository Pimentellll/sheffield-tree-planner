"""Verify freshly built artifacts from a clean, hash-locked installation."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import tomllib
import urllib.request
import venv

root = Path.cwd()
artifacts = Path(os.environ["ARTIFACT_DIR"])
version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
if os.environ["REF_TYPE"] == "tag":
    assert os.environ["REF_NAME"] == "v" + version, "tag/version mismatch"
wheels = list(artifacts.glob("*.whl"))
sdists = list(artifacts.glob("*.tar.gz"))
assert len(wheels) == len(sdists) == 1

with tempfile.TemporaryDirectory(
    prefix="canopy-installed-", dir=os.environ["RUNNER_TEMP"]
) as directory:
    clean = Path(directory)
    env = dict(os.environ)
    for key in (
        "PYTHONPATH",
        "CANOPY_LOCAL_MODEL_BASE",
        "CANOPY_LOCAL_MODEL",
        "CANOPY_LIVE_PROOF_DIR",
    ):
        env.pop(key, None)
    venv.create(clean / "venv", with_pip=True)
    python = clean / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    cli = (
        clean
        / "venv"
        / ("Scripts/sheffield-readiness.exe" if os.name == "nt" else "bin/sheffield-readiness")
    )

    def run(*args, capture=False, timeout=180):
        return subprocess.run(
            [str(x) for x in args],
            cwd=clean,
            env=env,
            check=True,
            text=True,
            capture_output=capture,
            timeout=timeout,
        ).stdout

    requirements = clean / "runtime-requirements.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--frozen",
            "--no-dev",
            "--no-emit-project",
            "--output-file",
            str(requirements),
        ],
        cwd=root,
        env=env,
        check=True,
    )
    run("uv", "pip", "install", "--python", python, "--require-hashes", "-r", requirements)
    run("uv", "pip", "install", "--python", python, "--no-deps", wheels[0])
    assert run(cli, "--version", capture=True).strip() == version
    run(cli, "--help", capture=True)
    receipt = json.loads(run(cli, "environment", capture=True))
    assert receipt["ok"] and receipt["scope"] == "environment_only"
    assert receipt["spark_verified"] is False and receipt["gpu_verified"] is False
    assert run(python, "-m", "tree_planner.api", "--version", capture=True).strip() == version
    run(python, "-m", "tree_planner.api", "--help", capture=True)
    for package in ("tree_planner", "sheffield_readiness"):
        location = run(
            python, "-c", f"import {package}; print({package}.__file__)", capture=True
        ).strip()
        assert Path(location).resolve().is_relative_to((clean / "venv").resolve())
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with (clean / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [
                str(python),
                "-m",
                "tree_planner.api",
                "--workspace",
                str(clean / "api"),
                "--port",
                str(port),
            ],
            cwd=clean,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while True:
                try:
                    with opener.open(
                        f"http://127.0.0.1:{port}/api/v1/health", timeout=1
                    ) as response:
                        health = json.load(response)
                    break
                except (OSError, ValueError):
                    assert server.poll() is None and time.monotonic() < deadline, (
                        "API failed to start"
                    )
                    time.sleep(0.1)
            assert (
                health["version"] == version
                and health["available_operations"] == []
                and health["worker_mode"] == "manual"
            )
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)
    demo = clean / "reference-demo"
    run(
        python,
        "-m",
        "tree_planner.evaluators.demo",
        "--output",
        demo,
        "--numerical-source",
        os.environ["CANOPY_NUMERICS_SOURCE"],
    )
    evidence = json.loads((demo / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "passed"
    checks = evidence["checks"]
    assert checks["positive_m2_h"] == 2.0 and checks["valid_zero_m2_h"] == 0.0
    for name in (
        "changed_revision_stales_old",
        "geometry_changes_fingerprint",
        "immutable_old_result",
        "changed_asset_job_failed_without_result",
        "failed_selection_clears_current",
        "restored_asset_recovered",
        "owned_server_stopped",
        "owned_worker_stopped",
    ):
        assert checks[name] is True, name
    assert (
        evidence["runs"]["failure"]["status"] == "failed"
        and evidence["runs"]["failure"]["run_id"] is None
    )
    proof = {
        "scope": "installed local API and synthetic one-tree calculation only; no model, Spark or scientific acceptance",
        "version": version,
        "environment": receipt,
        "api_health": health,
        "reference_checks": checks,
        "numerical_source_hashes": evidence["numerical_source_hashes"],
        "synthetic_inputs": evidence["synthetic_inputs"],
        "runs": {
            name: {
                "source_job_id": evidence["runs"][name]["source_job_id"],
                "run_id": evidence["runs"][name]["run_id"],
                "analytical_outcome": evidence["runs"][name]["analytical_outcome"],
                "input_snapshot_ref": evidence["runs"][name]["input_snapshot_ref"],
                "input_fingerprint": evidence["runs"][name]["input_fingerprint"],
                "provenance": evidence["runs"][name]["provenance"],
            }
            for name in ("positive", "zero", "recovery")
        },
        "failed_job": {
            key: evidence["runs"]["failure"][key] for key in ("job_id", "run_id", "status", "error")
        },
    }
    proof_path = artifacts / "installed-smoke.json"
    proof_path.write_text(json.dumps(proof, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("Installed readiness, API health and reference runtime checks passed")

files = sorted(wheels + sdists + [proof_path])
(artifacts / "SHA256SUMS").write_text(
    "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in files),
    encoding="utf-8",
)
