"""Synthetic boundary regression tests; no domain or numerical fixtures."""

import json
import unittest
from copy import deepcopy
from typing import Any

from boundary_probe import (
    BoundaryProbe,
    DefaultProbe,
    FrozenProbe,
    StrictTupleProbe,
    app,
    default_app,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


def sample() -> dict[str, Any]:
    """Return one clearly synthetic valid boundary input."""
    return {
        "schema_version": "0.1.0",
        "revision": 1,
        "cost_pence": 100,
        "unit": "m",
        "scope": "accepted",
        "timestamp": "2026-11-11T12:00:00Z",
        "nested": {"vector": [1, 2.0, 3], "value": 0.5},
        "note": None,
    }


class BoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_valid_json(self) -> None:
        response = self.client.post("/probe", json=sample())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sample())
        self.assertEqual(
            BoundaryProbe.model_validate_json(json.dumps(sample())).revision, 1
        )

    def test_invalid_boundary_values(self) -> None:
        cases = [(["nested", "unexpected"], 1), (["unexpected"], 1)]
        for field in ("revision", "cost_pence"):
            cases.extend(([field], value) for value in (True, "1", 1.0, -1))
        cases += [
            (["revision"], 0),
            (["schema_version"], "9"),
            (["unit"], "ft"),
            (["scope"], "other"),
            (["timestamp"], "2026-11-11T12:00:00+00:00"),
            (["timestamp"], "2026-02-30T12:00:00Z"),
            (["timestamp"], "bad"),
            (["nested", "vector"], [1, 2]),
            (["nested", "vector"], [1, 2, 3, 4]),
            (["nested", "vector"], "123"),
            (["nested", "vector"], [1, "2", 3]),
            (["nested", "vector"], [1, True, 3]),
            (["nested", "vector"], [1, float("nan"), 3]),
            (["nested", "value"], float("inf")),
            (["nested", "value"], float("-inf")),
            (["nested", "value"], True),
            (["nested", "value"], "1"),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                data = deepcopy(sample())
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                response = self.client.post(
                    "/probe",
                    content=json.dumps(data),
                    headers={"content-type": "application/json"},
                )
                self.assertEqual(response.status_code, 422, response.text)
                self.assertEqual(response.json(), {"detail": "Invalid request"})

    def test_malformed_and_hostile_input(self) -> None:
        for content in ("{", '{"nested": NaN}', '{"secret-hostile-marker": Infinity}'):
            with self.subTest(content=content):
                response = self.client.post(
                    "/probe",
                    content=content,
                    headers={"content-type": "application/json"},
                )
                self.assertEqual(response.status_code, 422)
                self.assertEqual(response.json(), {"detail": "Invalid request"})
                self.assertNotIn("secret-hostile-marker", response.text)

    def test_openapi_from_probe(self) -> None:
        schema = self.client.get("/openapi.json").json()
        schemas = schema["components"]["schemas"]
        top = schemas["BoundaryProbe"]
        nested = schemas["NestedProbe"]
        self.assertFalse(top["additionalProperties"])
        self.assertFalse(nested["additionalProperties"])
        self.assertIn("note", top["required"])
        self.assertIn({"type": "null"}, top["properties"]["note"]["anyOf"])
        self.assertEqual(nested["properties"]["vector"]["minItems"], 3)
        self.assertEqual(nested["properties"]["vector"]["maxItems"], 3)
        operation = schema["paths"]["/probe"]["post"]
        self.assertIn("BoundaryProbe", json.dumps(operation["requestBody"]))
        self.assertIn("BoundaryProbe", json.dumps(operation["responses"]["200"]))
        for mode in ("validation", "serialization"):
            generated = BoundaryProbe.model_json_schema(mode=mode)
            self.assertFalse(generated["additionalProperties"])
            self.assertIn("note", generated["required"])

    def test_defaults_and_shallow_frozen(self) -> None:
        default = DefaultProbe.model_validate({"revision": "1", "extra": 3})
        self.assertEqual(default.revision, 1)
        self.assertNotIn("extra", default.model_dump())
        frozen = FrozenProbe(values=[1])
        with self.assertRaises(ValidationError):
            frozen.values = [2]
        frozen.values.append(2)
        self.assertEqual(frozen.values, [1, 2])

    def test_strict_tuple_json_python_and_fastapi(self) -> None:
        raw = '{"values":[1,2,3]}'
        self.assertEqual(StrictTupleProbe.model_validate_json(raw).values, (1, 2, 3))
        with self.assertRaises(ValidationError):
            StrictTupleProbe.model_validate(json.loads(raw))
        tuple_app = FastAPI()

        @tuple_app.post("/tuple")
        def tuple_route(body: StrictTupleProbe) -> StrictTupleProbe:
            return body

        response = TestClient(tuple_app).post(
            "/tuple", content=raw, headers={"content-type": "application/json"}
        )
        self.assertEqual(response.status_code, 422)

    def test_required_nullable(self) -> None:
        data = sample()
        del data["note"]
        self.assertEqual(self.client.post("/probe", json=data).status_code, 422)
        data["note"] = None
        self.assertEqual(self.client.post("/probe", json=data).status_code, 200)

    def test_default_http_nonfinite_error_defect(self) -> None:
        data = sample()
        data["nested"]["value"] = float("nan")
        with self.assertRaises(ValueError):
            TestClient(default_app).post(
                "/probe",
                content=json.dumps(data),
                headers={"content-type": "application/json"},
            )


if __name__ == "__main__":
    unittest.main()
