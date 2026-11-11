# STP-002 synthetic validation-boundary probe

Independent draft experiment on the working contract at base revision `c94a5d2e86a30b2d04481aaf593bfd3c1af51713`; owner Ben. `BoundaryProbe`, its nested model and route are test-only synthetic examples, not accepted SiteBundle or Scenario definitions. No persisted scenarios, numerical evaluator, site data, production error contract or frontend types are implemented. Release impact: none. Work is advance development; event eligibility and shared contract acceptance remain unresolved.

From the repository root in Windows PowerShell, with uv and Python 3.11.15 available:

```powershell
uv venv --python 3.11.15 experiments/stp002_validation/.venv
uv pip install --python experiments/stp002_validation/.venv/Scripts/python.exe -r experiments/stp002_validation/requirements.txt
experiments/stp002_validation/.venv/Scripts/python.exe -m unittest discover -s experiments/stp002_validation -v
```

The exact resolved dependencies are pinned in `requirements.txt`. The isolated run used Python 3.11.15, Pydantic 2.13.4, FastAPI 0.133.1, HTTPX 0.28.1, and Starlette 1.10.0. Starlette emitted a TestClient deprecation warning concerning HTTPX; it did not prevent these checks. TestClient runs in process, without a listener.

Observations from this combination:

- Pydantic defaults coerce a numeric string to an integer and ignore unknown fields. The probe explicitly enables strict validation and forbids extras in each nested model; it also disables nonfinite floats and checks vector length and the narrow UTC spelling. JSON numbers that are integers are permitted for float vector components; bools and numeric strings are rejected.
- Pydantic strict tuple validation accepts a JSON array via `model_validate_json`, but rejects a decoded Python list; FastAPI's request path produces the latter behavior here. The probe uses a length-constrained list and tests the HTTP path. `frozen=True` prevents field reassignment but a nested list remains mutable; it is not evidence of immutable persisted revisions.
- The default FastAPI handler raises `ValueError` while serializing a validation error containing NaN. The separate test-only handler returns a constant bounded JSON 422 without reflecting input. It is not a proposed production error envelope, body-size limit, or complete transport security policy.
- OpenAPI is generated from the same models and tested for nested extra-field rules, vector length and required nullable input. Custom timestamp validation and finite-number behavior are not fully expressed by that schema; consumers must not treat OpenAPI alone as proof of runtime acceptance. Validation and serialization schemas can differ and should both be reviewed when actual contracts are generated.

Source rationale: Pydantic's [strict-mode documentation](https://docs.pydantic.dev/latest/concepts/strict_mode/) distinguishes Python and JSON validation; its [configuration reference](https://docs.pydantic.dev/latest/api/config/) documents extra-field, finite-number and shallow frozen behavior; its [JSON Schema guide](https://docs.pydantic.dev/latest/concepts/json_schema/) distinguishes validation and serialization schemas. The tests compare the library defaults with explicit controls rather than assuming those settings are already safe.

The checks do not establish STP-002, B01 or M2 completion, production compatibility, real-site validity, numerical accuracy, model inference or Spark operation. They do not test persistence, authorization, body limits, all timestamp variants, frontend generation or deployment. Before shared contract implementation, the three owners must acknowledge the working revision and producer/consumer meanings; the parent must arrange independent review and decide the production validation and error approach. No owner acceptance is inferred from this probe.
