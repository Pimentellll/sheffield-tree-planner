"""Adapter boundary checks independent of the optional numerical checkout."""

from datetime import datetime, timedelta, timezone
from threading import Event

import pytest

from tree_planner.evaluators import (
    ReferenceJobHandler,
    ReferenceProvider,
    ReferenceUnsupported,
    _check_stop,
)


def test_deadline_and_stop_are_checked():
    local, external = Event(), Event()
    past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
    with pytest.raises(ReferenceUnsupported, match="deadline"):
        _check_stop(local, external, past)
    external.set()
    with pytest.raises(ReferenceUnsupported, match="stopped"):
        _check_stop(local, external, future)
    external.clear()
    local.set()
    with pytest.raises(ReferenceUnsupported, match="stopped"):
        _check_stop(local, external, future)


def test_provider_requires_trusted_callables_and_source_hashes():
    def fn(*args, **kwargs):
        return None

    with pytest.raises(ValueError, match="source hashes"):
        ReferenceProvider(fn, fn, fn, "e", "1", "s", "1", ())
    with pytest.raises(ValueError, match="callables"):
        ReferenceProvider(fn, fn, None, "e", "1", "s", "1", (("ray", "a" * 64),))


def test_arbitrary_provider_is_not_implicitly_source_verified():
    def fn(*args, **kwargs):
        return None

    provider = ReferenceProvider(fn, fn, fn, "e", "1", "s", "1", (("ray", "a" * 64),))
    with pytest.raises(ReferenceUnsupported, match="verified implementation"):
        ReferenceJobHandler(provider).execution_hashes({}, operation="evaluate_layout")
