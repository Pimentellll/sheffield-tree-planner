"""Transport tests are mocked; the release proof exercises real localhost HTTP."""

import httpx
import pytest

from tree_planner.agents import ProtocolError
from tree_planner.contracts import ScenarioRef


def test_domain_http_transport_uses_host_task_headers_and_safe_errors():
    from tree_planner.agents.http import HTTPDispatcher

    observed = []

    def handle(request):
        observed.append(request)
        return httpx.Response(
            409,
            json={
                "code": "REVISION_CONFLICT",
                "message": "private source detail",
                "retryable": False,
                "field_errors": [],
                "details": {},
            },
        )

    dispatcher = HTTPDispatcher(
        "http://127.0.0.1:18000/api/v1",
        accepted_ref=ScenarioRef(scenario_id="accepted", revision=3, scope="accepted"),
        timeout_s=2,
        max_response_bytes=8192,
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises(ProtocolError, match="REVISION_CONFLICT") as exc:
        dispatcher.dispatch(
            {
                "request_id": "inspect",
                "operation": "inspect_site",
                "arguments": {"site_id": "site", "scene_revision": 1},
            }
        )
    assert "private source detail" not in str(exc.value)
    assert observed[0].headers["X-Canopy-Scenario-Id"] == "accepted"
    assert observed[0].headers["X-Canopy-Scenario-Revision"] == "3"


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/api/v1",
        "http://127.0.0.1:18000/api/v1?x=1",
        "http://user:secret@localhost/api/v1",
        "http://127.0.0.1:18000/other",
    ],
)
def test_domain_http_transport_refuses_nonlocal_or_ambiguous_bases(url):
    from tree_planner.agents.http import HTTPDispatcher

    with pytest.raises(ValueError):
        HTTPDispatcher(
            url,
            accepted_ref=ScenarioRef(scenario_id="accepted", revision=1, scope="accepted"),
            timeout_s=2,
            max_response_bytes=8192,
        )
