"""Exercise the local-only HTTP boundary, not a simulated planning result."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


def client(*, origins: tuple[str, ...] = ()) -> TestClient:
    from tree_planner.api.security import LocalOnlyMiddleware

    app = FastAPI()

    @app.get("/read")
    async def read() -> dict[str, str]:
        return {"scope": "security-test-only"}

    @app.post("/write")
    async def write(request: Request) -> dict[str, int]:
        return {"received_bytes": len(await request.body())}

    app.add_middleware(LocalOnlyMiddleware, allowed_origins=origins, max_body_bytes=64)
    return TestClient(app, base_url="http://127.0.0.1:8000")


def test_loopback_read_has_no_store_headers() -> None:
    with client() as connection:
        response = connection.get("/read")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "host", ["evil.example", "127.0.0.1.evil.example", "user@127.0.0.1", "127.0.0.1:99999"]
)
def test_foreign_or_malformed_host_is_rejected(host: str) -> None:
    with client() as connection:
        response = connection.get("/read", headers={"Host": host})
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_INPUT"


def test_mutation_requires_matching_origin() -> None:
    with client() as connection:
        missing = connection.post("/write", content=b"x")
        foreign = connection.post(
            "/write", content=b"x", headers={"Origin": "https://evil.example"}
        )
        valid = connection.post("/write", content=b"x", headers={"Origin": "http://127.0.0.1:8000"})
    assert missing.status_code == 403
    assert foreign.status_code == 403
    assert valid.status_code == 200 and valid.json()["received_bytes"] == 1


def test_explicit_loopback_frontend_origin_and_preflight() -> None:
    origin = "http://127.0.0.1:5173"
    with client(origins=(origin,)) as connection:
        response = connection.post("/write", content=b"x", headers={"Origin": origin})
        preflight = connection.options(
            "/write", headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in response.headers
    assert preflight.status_code == 204
    assert preflight.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    ["https://evil.example", "http://user@127.0.0.1:5173", "http://127.0.0.1:5173/path", "*"],
)
def test_frontend_origin_configuration_cannot_broaden_to_the_network(origin: str) -> None:
    with pytest.raises(ValueError):
        with client(origins=(origin,)) as connection:
            connection.get("/read")


def test_oversize_known_and_streamed_bodies_never_reach_application() -> None:
    origin = {"Origin": "http://127.0.0.1:8000"}
    with client() as connection:
        known = connection.post("/write", content=b"x" * 65, headers=origin)
        streamed = connection.post("/write", content=iter([b"x" * 40, b"y" * 40]), headers=origin)
    assert known.status_code == 413
    assert streamed.status_code == 413
    assert "received_bytes" not in known.json()
    assert "received_bytes" not in streamed.json()


def test_unbounded_content_length_is_rejected_without_integer_overflow() -> None:
    with client() as connection:
        response = connection.post(
            "/write",
            content=b"x",
            headers={"Origin": "http://127.0.0.1:8000", "Content-Length": "9" * 5000},
        )
    assert response.status_code == 413
    assert response.json()["code"] == "INVALID_INPUT"


def test_cross_origin_reads_and_unexpected_preflight_methods_are_rejected() -> None:
    with client() as connection:
        read = connection.get("/read", headers={"Origin": "https://evil.example"})
        preflight = connection.options(
            "/write",
            headers={"Origin": "http://127.0.0.1:8000", "Access-Control-Request-Method": "TRACE"},
        )
    assert read.status_code == 403
    assert preflight.status_code == 403
