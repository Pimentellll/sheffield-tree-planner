"""Structured model calls use explicit host controls and self-contained schemas."""

import json

import httpx
import pytest

from tree_planner.agents import ClientConfig, LocalClient, tool_schemas


def test_nested_tool_schema_is_self_contained_and_keeps_strict_types():
    schema = tool_schemas({"evaluate_layout"})[0]["function"]["parameters"]
    assert "$ref" not in json.dumps(schema)
    assert "$defs" not in json.dumps(schema)
    nested = schema["properties"]["layout_ref"]
    assert nested["type"] == "object"
    assert nested["additionalProperties"] is False
    assert nested["properties"]["revision"]["type"] == "integer"


def test_explicit_host_inference_controls_reach_the_local_request():
    seen = []

    def handler(request):
        seen.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"finish_reason": "stop", "message": {"role": "assistant", "content": "{}"}}
                ]
            },
        )

    cfg = ClientConfig(
        "http://127.0.0.1:11435/v1",
        "model",
        timeout_s=1,
        max_input_bytes=10000,
        max_response_bytes=1000,
        max_tokens=100,
        reasoning_effort="none",
        temperature=0,
    )
    LocalClient(cfg, transport=httpx.MockTransport(handler)).complete([], [])
    assert seen[0]["reasoning_effort"] == "none"
    assert seen[0]["temperature"] == 0


@pytest.mark.parametrize("value", [True, -1, float("nan"), 3])
def test_invalid_host_sampling_control_is_rejected(value):
    with pytest.raises(ValueError):
        ClientConfig(
            "http://127.0.0.1:11435/v1",
            "model",
            timeout_s=1,
            max_input_bytes=10000,
            max_response_bytes=1000,
            max_tokens=100,
            temperature=value,
        )
