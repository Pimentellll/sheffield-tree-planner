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


if __name__ == "__main__":
    unittest.main()
