"""An installed module command must execute, not silently exit at import."""

import subprocess
import sys


def test_reference_demo_module_has_a_real_cli_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "tree_planner.evaluators.demo", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--numerical-source" in result.stdout
    assert "--output" in result.stdout
