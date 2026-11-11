"""Local-only inference transport and tool round-trip diagnostic."""

import argparse
import http.client
import ipaddress
import json
import math
import platform
import secrets
import socket
import time
from importlib.metadata import version
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

DIST = "sheffield-tree-planner-readiness"
LIMIT = 1024 * 1024


class Failure(Exception):
    """A safe, classified diagnostic failure."""

    def __init__(self, stage: str, code: str) -> None:
        self.stage, self.code = stage, code


def inspect_runtime() -> dict:
    """Return local runtime facts and a fresh round-trip challenge."""
    return {
        "system": platform.system(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "nonce": secrets.token_urlsafe(24),
    }


def environment() -> dict:
    """Return a local environment receipt without hardware certification."""
    return {
        "scope": "environment_only",
        "ok": True,
        "system": platform.system(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "package_version": version(DIST),
        "spark_verified": False,
        "gpu_verified": False,
    }


def parse_url(value: str) -> str:
    """Validate and normalize a strictly loopback API base URL."""
    try:
        url = urlsplit(value)
        host, port = url.hostname, url.port
        if (
            url.scheme not in ("http", "https")
            or not host
            or url.username is not None
            or url.password is not None
            or "?" in value
            or "#" in value
            or url.path not in ("/v1", "/v1/")
            or port == 0
        ):
            raise ValueError()
        if host != "localhost" and not ipaddress.ip_address(host).is_loopback:
            raise ValueError()
        if not url.netloc or url.netloc.endswith(":"):
            raise ValueError()
        return urlunsplit((url.scheme, url.netloc, "/v1", "", ""))
    except ValueError:
        raise Failure("configuration", "invalid_endpoint") from None


def strict_json(raw: bytes | str) -> object:
    """Decode JSON while rejecting duplicate keys and nonfinite numbers."""

    def pairs(items: list) -> dict:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValueError()

    def finite_float(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise ValueError()
        return result

    return json.loads(
        raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float
    )


class NoRedirect(HTTPRedirectHandler):
    """Prevent a loopback request from forwarding to another endpoint."""

    def redirect_request(
        self,
        req: Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        """Reject every HTTP redirect."""
        return None


def request_json(url: str, payload: dict | None, timeout: float, stage: str) -> dict:
    """Send one bounded request with proxies and redirects disabled."""
    request = Request(
        url,
        data=None if payload is None else json.dumps(payload, allow_nan=False).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(
            request, timeout=timeout
        ) as response:
            lengths = response.headers.get_all("Content-Length", [])
            expected_length = None
            if lengths:
                value = lengths[0].strip()
                if (
                    len(lengths) != 1
                    or not value.isascii()
                    or not value.isdecimal()
                    or response.headers.get("Transfer-Encoding") is not None
                ):
                    raise Failure(stage, "response_error")
                expected_length = int(value)
                if expected_length > LIMIT:
                    raise Failure(stage, "response_error")
            raw = response.read(LIMIT + 1)
            # A size-limited read can silently return a valid JSON prefix on EOF.
            if expected_length is not None and len(raw) != expected_length:
                raise Failure(stage, "response_error")
        if len(raw) > LIMIT:
            raise Failure(stage, "response_error")
        value = strict_json(raw)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except HTTPError:
        raise Failure(stage, "http_error") from None
    except (URLError, TimeoutError, socket.timeout, ConnectionError, OSError):
        raise Failure(stage, "connection_timeout") from None
    except (ValueError, UnicodeError, RecursionError, http.client.HTTPException):
        raise Failure(stage, "response_error") from None


def validate_call(response: dict) -> tuple[dict, str]:
    """Validate the sole structured, empty-argument inspect_runtime call."""
    try:
        choices = response["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError()
        choice = choices[0]
        message = choice["message"]
        calls = message["tool_calls"]
        if (
            choice["finish_reason"] != "tool_calls"
            or message["role"] != "assistant"
            or not isinstance(calls, list)
            or len(calls) != 1
        ):
            raise ValueError()
        call = calls[0]
        function = call["function"]
        call_id = call["id"]
        args = function["arguments"]
        if (
            call["type"] != "function"
            or not isinstance(call_id, str)
            or not call_id.strip()
            or function["name"] != "inspect_runtime"
            or not isinstance(args, str)
            or strict_json(args) != {}
        ):
            raise ValueError()
        return message, call_id
    except (KeyError, TypeError, ValueError, RecursionError):
        raise Failure("first_completion", "invalid_tool") from None


def inference(
    base_url: str,
    model: str,
    timeout: float = 120,
    max_tokens: int = 2048,
    disable_thinking: bool = False,
) -> dict:
    """Check the selected local endpoint and complete a real tool observation round trip."""
    start = time.monotonic()
    base = parse_url(base_url)
    models = request_json(base + "/models", None, timeout, "models")
    data = models.get("data")
    if not isinstance(data, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("id"), str)
        for item in data
    ):
        raise Failure("models", "response_error")
    if model not in [item["id"] for item in data]:
        raise Failure("models", "unknown_model")
    models_elapsed = time.monotonic() - start
    tool = {
        "type": "function",
        "function": {
            "name": "inspect_runtime",
            "description": "Inspect the local runtime.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
    messages = [
        {
            "role": "user",
            "content": "Call inspect_runtime, then reply with only the nonce from its observation.",
        }
    ]
    payload = {
        "model": model,
        "messages": messages,
        "tools": [tool],
        "tool_choice": "auto",
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if disable_thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    first = request_json(
        base + "/chat/completions", payload, timeout, "first_completion"
    )
    assistant, call_id = validate_call(first)
    first_elapsed = time.monotonic() - start - models_elapsed
    observation = inspect_runtime()
    payload["messages"] = messages + [
        assistant,
        {"role": "tool", "tool_call_id": call_id, "content": json.dumps(observation)},
    ]
    payload["tool_choice"] = "none"
    second = request_json(
        base + "/chat/completions", payload, timeout, "second_completion"
    )
    try:
        choices = second["choices"]
        if not isinstance(choices, list) or len(choices) != 1:
            raise ValueError()
        choice = choices[0]
        message = choice["message"]
        if (
            choice["finish_reason"] != "stop"
            or message["role"] != "assistant"
            or message.get("tool_calls")
            or not isinstance(message.get("content"), str)
        ):
            raise ValueError()
        if message["content"].strip() != observation["nonce"]:
            raise Failure("second_completion", "nonce_mismatch")
    except (KeyError, TypeError, ValueError):
        raise Failure("second_completion", "response_error") from None
    total = time.monotonic() - start
    return {
        "scope": "transport_tool_smoke_only",
        "ok": True,
        "model": model,
        "tool_name": "inspect_runtime",
        "tool_roundtrip_verified": True,
        "application_domain_verified": False,
        "spark_verified": False,
        "timings_seconds": {
            "models": models_elapsed,
            "first_completion": first_elapsed,
            "second_completion_and_tool": total - models_elapsed - first_elapsed,
            "total": total,
        },
    }


def positive_float(value: str) -> float:
    """Parse a positive finite command-line number."""
    try:
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise ValueError()
        return number
    except ValueError:
        raise argparse.ArgumentTypeError("must be positive and finite") from None


def positive_int(value: str) -> int:
    """Parse a positive command-line integer."""
    try:
        number = int(value)
        if number <= 0:
            raise ValueError()
        return number
    except ValueError:
        raise argparse.ArgumentTypeError("must be a positive integer") from None


def main(argv: list[str] | None = None) -> int:
    """Run the command-line diagnostic and emit safe JSON receipts."""
    parser = argparse.ArgumentParser(prog="sheffield-readiness")
    parser.add_argument("--version", action="version", version=version(DIST))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("environment")
    check = commands.add_parser("inference")
    check.add_argument("--base-url", required=True)
    check.add_argument("--model", required=True)
    check.add_argument("--timeout", type=positive_float, default=120)
    check.add_argument("--max-tokens", type=positive_int, default=2048)
    check.add_argument("--disable-thinking", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = (
            environment()
            if args.command == "environment"
            else inference(
                args.base_url,
                args.model,
                args.timeout,
                args.max_tokens,
                args.disable_thinking,
            )
        )
        print(json.dumps(result, allow_nan=False))
        return 0
    except Failure as exc:
        print(json.dumps({"ok": False, "stage": exc.stage, "code": exc.code}))
        return 1
    except Exception:
        print(json.dumps({"ok": False, "stage": "internal", "code": "internal_error"}))
        return 1
