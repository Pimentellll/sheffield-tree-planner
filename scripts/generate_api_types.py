"""Deterministic domain and implemented HTTP schemas/types from backend authority.

openapi.json remains the route-free domain catalogue. http-openapi.json is
derived from the actual local app, never handwritten endpoint declarations.
Unknown schema constructs are errors, never silently widened to `any`.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))
from tree_planner import contracts  # noqa: E402


def typescript_type(schema):
    allowed = {
        "title",
        "description",
        "$ref",
        "type",
        "const",
        "enum",
        "anyOf",
        "oneOf",
        "discriminator",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "prefixItems",
        "minItems",
        "maxItems",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "maxLength",
        "pattern",
        "default",
        "propertyNames",
        "patternProperties",
    }
    unknown = set(schema) - allowed
    if unknown:
        raise ValueError(f"unsupported schema keywords: {sorted(unknown)}")
    if "propertyNames" in schema:
        # String key restrictions remain runtime schema rules, but still validate syntax.
        if schema["propertyNames"] != {"minLength": 1}:
            raise ValueError("unsupported non-string dictionary key")
    if "patternProperties" in schema:
        # Pydantic's exact representation for dict[ID, T]. Key validity stays
        # a backend rule, as with string/number constraints elsewhere in TS.
        patterns = schema["patternProperties"]
        if set(patterns) != {r"\S"} or schema.get("type") != "object" or schema.get("properties"):
            raise ValueError("unsupported patterned object")
        return "Readonly<Record<string, " + typescript_type(patterns[r"\S"]) + ">>"
    if "$ref" in schema:
        ref = schema["$ref"]
        if not re.fullmatch(r"#/\$defs/[A-Za-z_][A-Za-z_0-9]*", ref):
            raise ValueError(f"unsupported reference: {ref}")
        return ref.rsplit("/", 1)[1]
    if "const" in schema:
        return json.dumps(schema["const"])
    if "enum" in schema:
        return " | ".join(json.dumps(v) for v in schema["enum"])
    for union in ("anyOf", "oneOf"):
        if union in schema:
            return "(" + " | ".join(typescript_type(s) for s in schema[union]) + ")"
    kind = schema.get("type")
    if kind in {"integer", "number"}:
        return "number"
    if kind == "string":
        return "string"
    if kind == "boolean":
        return "boolean"
    if kind == "null":
        return "null"
    if kind == "array":
        if "prefixItems" in schema:
            count = len(schema["prefixItems"])
            if schema.get("minItems") != count or schema.get("maxItems") != count:
                raise ValueError("unsupported variable-length prefix tuple")
            return "readonly [" + ", ".join(typescript_type(s) for s in schema["prefixItems"]) + "]"
        if "items" not in schema:
            raise ValueError("array items must be explicit")
        return "ReadonlyArray<" + typescript_type(schema["items"]) + ">"
    if kind == "object":
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict) and not properties:
            return "Readonly<Record<string, " + typescript_type(additional) + ">>"
        if additional is not False:
            raise ValueError("open or mixed objects unsupported")
        required = set(schema.get("required", []))
        fields = [
            f"readonly {json.dumps(k)}{'' if k in required else '?'}: {typescript_type(v)};"
            for k, v in sorted(properties.items())
        ]
        return "{ " + " ".join(fields) + " }" if fields else "Readonly<Record<string, never>>"
    raise ValueError(f"unsupported schema type: {kind!r}")


def public_models():
    return {
        name: getattr(contracts, name)
        for name in sorted(contracts.__all__)
        if isinstance(getattr(contracts, name), type)
        and issubclass(getattr(contracts, name), BaseModel)
        and name != "ContractModel"
    }


def artifacts():
    models = public_models()
    _, document = models_json_schema(
        [(model, "validation") for model in models.values()], ref_template="#/$defs/{model}"
    )
    definitions = document["$defs"]
    if set(models) != set(definitions):
        raise ValueError("all nested models must have stable named public exports")
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "CANOPY domain contract catalogue 0.1.0",
        "$defs": definitions,
    }
    ts = [
        "// Generated by scripts/generate_api_types.py from Pydantic models. DO NOT EDIT.",
        "// Runtime constraints (finite values, revisions, references, rights) require backend validation.",
        f"export const SCHEMA_VERSION = {json.dumps(contracts.SCHEMA_VERSION)} as const;",
        "",
    ]
    for name, definition in sorted(definitions.items()):
        ts.append(f"export type {name} = {typescript_type(definition)};")

    def openapi_refs(obj):
        if isinstance(obj, dict):
            return {k: openapi_refs(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [openapi_refs(v) for v in obj]
        if isinstance(obj, str):
            return obj.replace("#/$defs/", "#/components/schemas/")
        return obj

    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": "CANOPY domain schema catalogue",
            "version": contracts.SCHEMA_VERSION,
            "description": "Serialization schemas only. No implemented HTTP routes are claimed.",
        },
        "paths": {},
        "components": {"schemas": openapi_refs(definitions)},
    }

    def dump(value):
        return (
            json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        )

    from tree_planner.api import create_app

    # Construction uses an isolated SQLite workspace, not a worker or private data.
    with TemporaryDirectory(prefix="canopy-schema-", dir=os.environ.get("TMPDIR")) as temp:
        # Windows may return an 8.3 alias; canonicalize only this generator-owned workspace.
        http = create_app(Path(temp).resolve(strict=True), start_worker=False).openapi()

    definitions_http = http["components"]["schemas"]
    type_names = {}
    for name in definitions_http:
        if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name):
            type_names[name] = name
        elif re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*-(Input|Output)", name):
            # Preserve exact wire schema keys; map only Pydantic's documented
            # input/output suffix into a valid, collision-checked TS identifier.
            type_names[name] = name.replace("-", "_")
        else:
            raise ValueError("unsupported HTTP model name")
    if len(set(type_names.values())) != len(type_names):
        raise ValueError("HTTP type identifier collision")

    def domain_refs(value):
        if isinstance(value, dict):
            return {key: domain_refs(item) for key, item in value.items()}
        if isinstance(value, list):
            return [domain_refs(item) for item in value]
        if isinstance(value, str) and value.startswith("#/components/schemas/"):
            name = value.removeprefix("#/components/schemas/")
            return "#/$defs/" + type_names[name]
        return value

    http_ts = [
        "// Generated from the implemented backend HTTP schemas. DO NOT EDIT.",
        "// Pydantic -Input/-Output wire names use _Input/_Output TS suffixes.",
        "",
    ]
    for name, definition in sorted(definitions_http.items()):
        http_ts.append(
            f"export type {type_names[name]} = {typescript_type(domain_refs(definition))};"
        )

    return {
        "contracts.schema.json": dump(schema),
        "openapi.json": dump(openapi),
        "contracts.ts": "\n".join(ts) + "\n",
        "http-openapi.json": dump(http),
        "http.ts": "\n".join(http_ts) + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if checked-in output differs")
    args = parser.parse_args()
    output = ROOT / "generated"
    for name, content in artifacts().items():
        path = output / name
        if args.check:
            if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
                raise SystemExit(f"generated artifact differs: {path}")
        else:
            output.mkdir(exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
        print(f"{'checked' if args.check else 'generated'} {path}")


if __name__ == "__main__":
    main()
