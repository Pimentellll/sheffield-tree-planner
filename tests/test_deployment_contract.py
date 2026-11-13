"""Check deployment-document invariants without downloading or running a model."""

import json
from pathlib import Path
import re
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentContractTests(unittest.TestCase):
    def test_pinned_profile_matches_recipe(self):
        profile = json.loads((ROOT / "deploy/spark/model-profile.json").read_text())
        recipe = (ROOT / "deploy/spark/inference.compose.yml").read_text()
        self.assertEqual(profile["status"], "candidate_not_device_tested")
        self.assertEqual(profile["image_metadata"]["architecture"], "arm64")
        self.assertEqual(profile["image_metadata"]["os"], "linux")
        self.assertIn("nvcr.io/nvidia/vllm@" + profile["image_arm64_digest"], recipe)
        self.assertIn("platform: linux/arm64", recipe)
        self.assertIn('"127.0.0.1:8000:8000"', recipe)
        for field in (
            "served_model_name",
            "tool_call_parser",
            "reasoning_parser",
            "max_model_len",
            "max_num_seqs",
            "gpu_memory_utilization",
        ):
            self.assertIn(str(profile[field]), recipe)
        self.assertNotIn("network_mode: host", recipe)
        self.assertNotIn("privileged:", recipe)
        self.assertNotIn("docker.sock", recipe)
        expected = {w["file"]: w["sha256"] for w in profile["weights"]}
        expected.update(
            {
                name: details["sha256"]
                for name, details in profile["code_and_configuration"].items()
            }
        )
        actual = {}
        for line in (ROOT / "deploy/spark/model.sha256").read_text().splitlines():
            digest, path = line.split("  ", 1)
            self.assertRegex(digest, r"^[a-f0-9]{64}$")
            actual[path.removeprefix("models/nemotron-nano/")] = digest
        self.assertEqual(actual, expected)
        self.assertEqual(
            sum(w["bytes"] for w in profile["weights"]), profile["weight_bytes"]
        )

    def test_local_document_links_and_release_record(self):
        documents = [
            ROOT / "README.md",
            ROOT / "CHANGELOG.md",
            *sorted((ROOT / "docs").rglob("*.md")),
        ]
        for document in documents:
            for target in re.findall(
                r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")
            ):
                if "://" in target or target.startswith(("#", "mailto:")):
                    continue
                with self.subTest(document=document.name, target=target):
                    self.assertTrue(
                        (document.parent / target.split("#", 1)[0]).exists()
                    )
        version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
            "version"
        ]
        self.assertIn(
            "## " + version + " — unreleased",
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
        )
        ssh = (ROOT / "deploy/spark/ssh_config.example").read_text()
        for expected in (
            "HostName spark.example.invalid",
            "ForwardAgent no",
            "IdentitiesOnly yes",
            "StrictHostKeyChecking ask",
            "ExitOnForwardFailure yes",
        ):
            self.assertIn(expected, ssh)


class ApplicationDeploymentTests(unittest.TestCase):
    """The shipped Spark config must be one the control script and backend accept."""

    def test_application_env_matches_loader_and_ports(self):
        values = {}
        for line in (ROOT / "deploy/spark/application.env.example").read_text().splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                values[key] = value
        script = (ROOT / "deploy/spark/canopyctl").read_text()
        allowed = re.search(r"\n\s+(CANOPY_PORT\|[A-Z_|]+)\)", script).group(1).split("|")
        self.assertEqual(set(values), set(allowed))
        self.assertNotEqual(values["CANOPY_PORT"], "8000")  # 8000 is the model service
        self.assertIn('"127.0.0.1:8000:8000"', (ROOT / "deploy/spark/inference.compose.yml").read_text())
        self.assertEqual(values["LLM_MODEL"], json.loads(
            (ROOT / "deploy/spark/model-profile.json").read_text())["served_model_name"])
        try:
            from tree_planner.agents.runs import AgentSettings
        except ImportError:  # readiness-only environment without the backend installed
            self.skipTest("backend package not installed")
        settings = AgentSettings.from_env("http://127.0.0.1:8765/api/v1", values)
        self.assertEqual(settings.client_config().chat_template_kwargs, {"enable_thinking": False})

    def test_control_script_never_exposes_or_administers(self):
        script = (ROOT / "deploy/spark/canopyctl").read_text()
        self.assertNotIn("0.0.0.0", script)
        for forbidden in ("docker compose", "docker run", "docker pull", "sudo ", "ssh-keygen",
                          "authorized_keys", "hf download", "StrictHostKeyChecking=no"):
            self.assertNotIn(forbidden, script)
        bundle = (ROOT / "deploy/spark/make_bundle.sh").read_text()
        self.assertIn("git archive", bundle)
        self.assertIn("--require-hashes", bundle)


if __name__ == "__main__":
    unittest.main()
