"""Shared guards for site tests."""

from __future__ import annotations

import ipaddress
import socket
import urllib.request

import pytest


def _is_local(address) -> bool:
    """Unix-domain paths and loopback IP literals only; host names are never resolved here."""
    if isinstance(address, (str, bytes)):
        return True
    if isinstance(address, tuple) and address:
        host = address[0]
        if host == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False
    return False


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Guard against site tests reaching a real endpoint (for example the council layer).

    Blocks ``urllib.request.urlopen`` and ``OpenerDirector.open`` outright, and
    ``socket.socket.connect``/``connect_ex`` to anything but loopback or a Unix socket
    (in-process test clients and the event loop's own socket pair stay allowed). Not
    intercepted: DNS lookups (``getaddrinfo``) before a refused connect, and UDP
    ``sendto``/``sendmsg``. Attempts
    are recorded and fail the test afterwards, because code under test such as
    ``prepare_tree_inventory.fetch`` would otherwise turn the stub's error into a
    SystemExit that an expected-failure assertion could swallow.
    """
    attempts = []
    real_connect, real_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def refuse(*args, **kwargs):
        attempts.append(("urllib", args))
        raise OSError("network disabled in site tests")

    def guarded_connect(self, address):
        if not _is_local(address):
            attempts.append(("socket.connect", address))
            raise OSError("network disabled in site tests")
        return real_connect(self, address)

    def guarded_connect_ex(self, address):
        if not _is_local(address):
            attempts.append(("socket.connect_ex", address))
            raise OSError("network disabled in site tests")
        return real_connect_ex(self, address)

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(urllib.request.OpenerDirector, "open", refuse)
    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", guarded_connect_ex)
    yield
    assert not attempts, f"a test attempted a real network request: {attempts!r}"
