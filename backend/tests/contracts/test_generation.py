"""Generation checks operate on backend model schemas, not duplicate wire types."""

import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def generator():
    spec = importlib.util.spec_from_file_location(
        "generate_api_types", ROOT / "scripts/generate_api_types.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checked_in_artifacts_are_deterministic(tmp_path):
    gen = generator()
    first, second = gen.artifacts(), gen.artifacts()
    assert first == second
    assert set(first) == {
        "openapi.json",
        "contracts.schema.json",
        "contracts.ts",
        "http-openapi.json",
        "http.ts",
    }
    for name, content in first.items():
        assert (ROOT / "generated" / name).read_bytes() == content.encode("utf-8")
    schema = json.loads(first["contracts.schema.json"])
    assert schema["$defs"]["ScenarioRef"]["additionalProperties"] is False
    assert json.loads(first["openapi.json"])["paths"] == {}


def test_generator_canonicalizes_its_owned_temporary_workspace(tmp_path, monkeypatch):
    gen = generator()
    workspace = tmp_path / "owned-workspace"
    anchor = workspace / "anchor"
    anchor.mkdir(parents=True)
    alias = anchor / ".."
    assert alias.absolute() != workspace.resolve(strict=True)

    @contextmanager
    def owned_temporary_directory(**kwargs):
        # Exercise the same noncanonical-root boundary without requiring NTFS aliases.
        assert kwargs["prefix"] == "canopy-schema-"
        yield str(alias)

    monkeypatch.setattr(gen, "TemporaryDirectory", owned_temporary_directory)
    emitted = gen.artifacts()
    for name, content in emitted.items():
        assert (ROOT / "generated" / name).read_bytes() == content.encode("utf-8")


def test_http_contracts_are_derived_from_the_implemented_routes():
    emitted = generator().artifacts()
    http = json.loads(emitted["http-openapi.json"])
    assert "/api/v1/jobs" in http["paths"]
    assert "/api/v1/operations" in http["paths"]
    assert http["components"]["schemas"]["SiteInspection"]["additionalProperties"] is False
    assert "export type ScenarioSelections" in emitted["http.ts"]
    assert "export type SiteInspection" in emitted["http.ts"]


@pytest.mark.parametrize(
    "schema",
    [
        {"allOf": [{"type": "string"}]},
        {"type": "object", "patternProperties": {"x": {"type": "string"}}},
        {"type": "integer", "inventedKeyword": True},
        {"$ref": "https://example.com/schema"},
    ],
)
def test_unsupported_construct_fails_loudly(schema):
    with pytest.raises(ValueError):
        generator().typescript_type(schema)
