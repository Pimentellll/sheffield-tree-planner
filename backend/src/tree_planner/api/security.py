"""Loopback-only, explicitly originated, bounded JSON HTTP transport.

This protects a single-user local application from foreign web origins. It is
not authentication against another process running as the same OS user.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from starlette.datastructures import Headers
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_HOST = re.compile(r"(?:127\.0\.0\.1|localhost|\[::1\])(?::([0-9]{1,5}))?", re.I)
_METHODS = {"GET", "POST", "PUT", "DELETE", "OPTIONS"}


def _origin(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not _HOST.fullmatch(parsed.netloc)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Only explicit loopback origins without paths are supported")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid loopback origin port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid loopback origin port")
    return f"{parsed.scheme}://{parsed.netloc.lower()}"


class LocalOnlyMiddleware:
    """Reject unsafe hosts/origins and buffer at most the declared JSON bound."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        allowed_origins: tuple[str, ...] = (),
        max_body_bytes: int = 1_048_576,
    ) -> None:
        if type(max_body_bytes) is not int or max_body_bytes < 1:
            raise ValueError("HTTP body bound must be a positive integer")
        self.app = app
        self.allowed_origins = {_origin(value) for value in allowed_origins}
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)

        async def fail(status: int, message: str) -> None:
            response = JSONResponse(
                {
                    "code": "INVALID_INPUT",
                    "message": message,
                    "retryable": False,
                    "field_errors": [],
                    "details": {},
                },
                status_code=status,
                headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
            )
            await response(scope, receive, send)

        host = headers.get("host", "")
        match = _HOST.fullmatch(host)
        if match is None or (match.group(1) and not 1 <= int(match.group(1)) <= 65535):
            await fail(400, "Invalid local Host header")
            return
        same_origin = f"{scope.get('scheme', 'http')}://{host.lower()}"
        supplied_origin = headers.get("origin")
        if supplied_origin is not None:
            try:
                normalized_origin = _origin(supplied_origin)
            except ValueError:
                normalized_origin = ""
            if normalized_origin not in self.allowed_origins | {same_origin}:
                await fail(403, "Origin is not permitted")
                return
        elif scope["method"] not in {"GET", "HEAD", "OPTIONS"}:
            await fail(403, "A permitted Origin is required for mutations")
            return
        if scope["method"] == "OPTIONS":
            if (
                supplied_origin is None
                or headers.get("access-control-request-method") not in _METHODS
            ):
                await fail(403, "Preflight is not permitted")
                return
            response = Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": supplied_origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, If-Match",
                    "Vary": "Origin",
                    "Cache-Control": "no-store",
                },
            )
            await response(scope, receive, send)
            return
        length = headers.get("content-length")
        if length is not None and (not length.isascii() or not length.isdecimal()):
            await fail(400, "Invalid Content-Length")
            return
        normalized_length = (length.lstrip("0") or "0") if length is not None else None
        bound = str(self.max_body_bytes)
        if normalized_length is not None and (
            len(normalized_length) > len(bound)
            or (len(normalized_length) == len(bound) and normalized_length > bound)
        ):
            await fail(413, "Request body exceeds the local size limit")
            return
        declared_length = int(normalized_length) if normalized_length is not None else None
        messages: list[Message] = []
        size = 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                await fail(400, "Invalid HTTP request stream")
                return
            size += len(message.get("body", b""))
            if size > self.max_body_bytes:
                await fail(413, "Request body exceeds the local size limit")
                return
            messages.append(message)
            if not message.get("more_body", False):
                break
        if declared_length is not None and declared_length != size:
            await fail(400, "Content-Length does not match the request body")
            return
        index = 0

        async def replay() -> Message:
            nonlocal index
            if index < len(messages):
                message = messages[index]
                index += 1
                return message
            return await receive()

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = [
                    (k, v)
                    for k, v in message.get("headers", [])
                    if k.lower()
                    not in {
                        b"cache-control",
                        b"x-content-type-options",
                        b"access-control-allow-origin",
                    }
                ]
                response_headers.extend(
                    [(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")]
                )
                if supplied_origin is not None:
                    response_headers.extend(
                        [
                            (b"access-control-allow-origin", supplied_origin.encode("ascii")),
                            (b"vary", b"Origin"),
                        ]
                    )
                message = {**message, "headers": response_headers}
            await send(message)

        await self.app(scope, replay, secured_send)
