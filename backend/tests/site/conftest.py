"""Shared guards for site tests."""

from __future__ import annotations

import urllib.request

import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """No site test may reach a real endpoint (for example the council layer) through urllib.

    Covers ``urllib.request.urlopen`` and ``OpenerDirector.open`` only; raw sockets or other
    HTTP clients are not intercepted. Attempts are recorded and fail the test afterwards, because code under test such as
    ``prepare_tree_inventory.fetch`` would otherwise turn the stub's error into a
    SystemExit that an expected-failure assertion could swallow.
    """
    attempts = []

    def refuse(*args, **kwargs):
        attempts.append(args)
        raise OSError("network disabled in site tests")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", refuse)
    yield
    assert not attempts, f"a test attempted a real network request: {attempts!r}"
