"""Exercise the actual workflow shell step with disposable local fake servers."""

import os
import pathlib
import signal
import socket
import subprocess
import sys
import tempfile
import textwrap
import time


def listening(port):
    with socket.socket() as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def owned_process(pid, server):
    if os.name == "nt":
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}').CommandLine"],
            capture_output=True, text=True, check=False,
        )
        return str(server).lower() in result.stdout.lower()
    try:
        return str(server).encode() in pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    except FileNotFoundError:
        return False


def main():
    workflow = pathlib.Path(__file__).resolve().parents[1] / "workflows/frontend.yml"
    data = workflow.read_text(encoding="utf-8")
    step = data.split("      - name: Integrated browser checks\n", 1)[1]
    script = textwrap.dedent(step.split("        run: |\n", 1)[1].split("      - name:", 1)[0])
    if any(listening(port) for port in (8765, 5173)):
        raise RuntimeError("test ports are already occupied")

    with tempfile.TemporaryDirectory(prefix="canopy-lifecycle-", dir=os.environ.get("RUNNER_TEMP")) as temp:
        root = pathlib.Path(temp)
        (root / ".venv/bin").mkdir(parents=True)
        (root / "bin").mkdir()
        (root / "frontend").mkdir()
        server = root / "server.py"
        server.write_text(textwrap.dedent('''\
            import http.server, os, pathlib, subprocess, sys
            role = sys.argv[1]
            with pathlib.Path(os.environ["RUNNER_TEMP"], role + ".pid").open("a") as pids:
                pids.write(str(os.getpid()) + "\\n")
            if os.environ["FAIL_AT"] == role:
                raise SystemExit(42)
            if role == "frontend":
                child = subprocess.Popen([sys.executable, "-c", "import sys; sys.stdin.buffer.read()", __file__],
                                         stdin=subprocess.PIPE)
                with pathlib.Path(os.environ["RUNNER_TEMP"], "child.pid").open("a") as pids:
                    pids.write(str(child.pid) + "\\n")
            class Handler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.end_headers()
                def log_message(self, *args):
                    pass
            http.server.HTTPServer(("127.0.0.1", 8765 if role == "backend" else 5173), Handler).serve_forever()
        '''), encoding="utf-8")
        backend = root / ".venv/bin/python"
        backend.write_text('#!/usr/bin/env bash\nexec "$TEST_PYTHON" "$FAKE_SERVER" backend\n', encoding="utf-8")
        node = root / "bin/node"
        node.write_text(textwrap.dedent('''\
            #!/usr/bin/env bash
            if [[ "$1" == *vite.js ]]; then exec "$TEST_PYTHON" "$FAKE_SERVER" frontend; fi
            echo check >> "$RUNNER_TEMP/checks"
            [[ "$FAIL_AT" != browser ]]
        '''), encoding="utf-8")
        backend.chmod(0o755)
        node.chmod(0o755)
        step_file = root / "step.sh"
        step_file.write_text(script, encoding="utf-8")
        for scenario in ("backend", "frontend", "browser", "success"):
            run = root / ("case-" + scenario)
            run.mkdir()
            env = os.environ.copy()
            env.update(PATH=str(root / "bin") + os.pathsep + env["PATH"],
                       RUNNER_TEMP=str(run), TEST_PYTHON=sys.executable,
                       FAKE_SERVER=str(server), FAIL_AT=scenario)
            try:
                result = subprocess.run([os.environ.get("CANOPY_TEST_BASH", "bash"), str(step_file)], cwd=root, env=env,
                                        capture_output=True, text=True, timeout=90)
                expected_checks = 2 if scenario == "success" else 1 if scenario == "browser" else 0
                checks = (run / "checks").read_text().count("check") if (run / "checks").exists() else 0
                expected_roles = {"backend"} if scenario == "backend" else {"backend", "frontend"}
                if scenario in ("browser", "success"):
                    expected_roles.add("child")
                roles = {p.stem for p in run.glob("*.pid")}
                if ((result.returncode == 0) != (scenario == "success") or
                        checks != expected_checks or roles != expected_roles):
                    raise AssertionError((scenario, result.returncode, checks, result.stdout, result.stderr))
                time.sleep(0.5)
                if any(listening(port) for port in (8765, 5173)):
                    raise AssertionError(f"{scenario}: listener survived cleanup")
                pids = [int(pid) for p in run.glob("*.pid") for pid in p.read_text().splitlines()]
                if any(owned_process(pid, server) for pid in pids):
                    raise AssertionError(f"{scenario}: owned server survived cleanup")
                print(f"{scenario}: exit={result.returncode}, browser checks={checks}, listeners closed")
            finally:
                # Only PIDs recorded by this test are eligible for emergency cleanup.
                for pid_file in run.glob("*.pid"):
                    for value in pid_file.read_text().splitlines():
                        pid = int(value)
                        if not owned_process(pid, server):
                            continue
                        if os.name == "nt":
                            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"],
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        else:
                            try:
                                os.kill(pid, signal.SIGTERM)
                            except ProcessLookupError:
                                pass


if __name__ == "__main__":
    main()
