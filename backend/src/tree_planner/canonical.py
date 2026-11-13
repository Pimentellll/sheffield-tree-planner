"""Server-owned canonical JSON identity for complete immutable inputs.

Object keys are sorted; array order, Unicode, case, and JSON numeric kinds are
preserved. Callers supply model_dump(mode="json") output rather than Python
objects or display strings. This is a project convention, not RFC 8785 JCS.
"""

from __future__ import annotations

import hashlib
import json
import math


def _validate(value: object) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("Canonical snapshots require finite numbers")
        return
    if type(value) is list:
        for item in value:
            _validate(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("Canonical snapshots require JSON string object keys")
            _validate(item)
        return
    raise ValueError("Canonical snapshots require JSON values without coercion")


def canonical_bytes(value: object) -> bytes:
    """Serialize finite JSON deterministically without changing identifiers."""
    _validate(value)
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def content_hash(value: object) -> str:
    """Return SHA-256 over the server's exact canonical JSON representation."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
