"""Loopback-only domain transport with a host-pinned accepted task."""

from __future__ import annotations

import ipaddress
import math
from urllib.parse import quote, urlsplit

import httpx
from pydantic import ValidationError

from tree_planner.contracts import (
    ContractError,
    Job,
    OperationEnvelope,
    Result,
    Scenario,
    ScenarioRef,
    Selection,
    SiteInspection,
)
from . import ProtocolError, _json


class HTTPDispatcher:
    """Call the implemented local API; a model cannot choose its task headers."""

    def __init__(
        self,
        base_url: str,
        *,
        accepted_ref: ScenarioRef,
        timeout_s: float,
        max_response_bytes: int,
        transport=None,
    ):
        try:
            url = urlsplit(base_url)
            local = (
                url.hostname == "localhost" or ipaddress.ip_address(url.hostname or "").is_loopback
            )
            valid = (
                url.scheme in {"http", "https"}
                and local
                and url.username is None
                and url.password is None
                and not url.query
                and not url.fragment
                and url.path.rstrip("/") == "/api/v1"
                and (url.port is None or 0 < url.port < 65536)
            )
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("An unambiguous loopback CANOPY API base is required")
        if type(timeout_s) not in (int, float) or not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("A positive finite timeout is required")
        if type(max_response_bytes) is not int or max_response_bytes <= 0:
            raise ValueError("A positive response byte bound is required")
        self.accepted_ref = ScenarioRef.model_validate(accepted_ref)
        if self.accepted_ref.scope != "accepted":
            raise ValueError("The host must select an accepted task")
        self.max_response_bytes = max_response_bytes
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            timeout=timeout_s,
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={
                "Origin": f"{url.scheme}://{url.netloc}",
                "X-Canopy-Scenario-Id": self.accepted_ref.scenario_id,
                "X-Canopy-Scenario-Revision": str(self.accepted_ref.revision),
            },
        )
        self.trace: list[dict] = []

    def close(self) -> None:
        """Release the transport and its connections."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _request(self, method: str, path: str, *, payload=None, params=None) -> dict:
        try:
            with self._client.stream(method, path, json=payload, params=params) as response:
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > self.max_response_bytes:
                        raise ProtocolError("domain response byte limit")
                status = response.status_code
                data = _json(bytes(body))
        except ProtocolError:
            raise
        except (httpx.HTTPError, ValueError, UnicodeError) as exc:
            raise ProtocolError("domain HTTP transport failed") from exc
        self.trace.append({"method": method, "path": path, "status": status, "response": data})
        if type(data) is not dict:
            raise ProtocolError("domain response is not an object")
        if not 200 <= status < 300:
            try:
                error = ContractError.model_validate(data)
            except ValidationError as exc:
                raise ProtocolError("invalid domain error response") from exc
            raise ProtocolError("domain operation failed: " + error.code)
        return data

    def scenario(self, ref: ScenarioRef) -> Scenario:
        """Fetch an exact immutable snapshot, never a latest-revision fallback."""
        data = self._request(
            "GET",
            "scenarios/" + quote(ref.scenario_id, safe=""),
            params={"revision": ref.revision, "scope": ref.scope},
        )
        scenario = Scenario.model_validate(data)
        if (scenario.scenario_id, scenario.revision, scenario.scope) != (
            ref.scenario_id,
            ref.revision,
            ref.scope,
        ):
            raise ProtocolError("domain scenario identity mismatch")
        return scenario

    def _scope(self, ref: ScenarioRef) -> None:
        if ref != self.accepted_ref:
            scenario = self.scenario(ref)
            if scenario.scope != "hypothetical" or scenario.base_scenario_ref != self.accepted_ref:
                raise ProtocolError("domain result is outside the accepted task")

    def dispatch(self, envelope):
        """Send only the strict operation envelope with fixed host context headers."""
        envelope = OperationEnvelope.model_validate(envelope)
        data = self._request("POST", "operations", payload=envelope.model_dump(mode="json"))
        operation = envelope.root.operation
        if operation == "inspect_site":
            return SiteInspection.model_validate(data)
        if operation == "prepare_scenario":
            return Scenario.model_validate(data)
        return Job.model_validate(data)

    def poll(self, job_id: str) -> Job:
        """Read stored job state and enforce the host investigation scope."""
        job = Job.model_validate(self._request("GET", "jobs/" + quote(job_id, safe="")))
        self._scope(
            ScenarioRef(
                scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
            )
        )
        return job

    def result(self, run_id: str) -> Result:
        """Read immutable evidence; delivery is checked separately by AgentLoop."""
        result = Result.model_validate(self._request("GET", "results/" + quote(run_id, safe="")))
        self._scope(result.input_snapshot_ref)
        return result

    def selection(self, ref: ScenarioRef, slot: str) -> Selection:
        """Read selection sequence and origin from the server, not response order."""
        self._scope(ref)
        data = self._request(
            "GET",
            "scenarios/" + quote(ref.scenario_id, safe="") + "/selections",
            params={"revision": ref.revision, "scope": ref.scope},
        )
        if slot not in {"evaluation", "search", "comparison"}:
            raise ProtocolError("unknown selection slot")
        state = data.get(slot)
        if type(state) is dict and state.get("selection") is not None:
            selection = Selection.model_validate(state["selection"])
            if selection.scenario_ref != ref or selection.view_slot != slot:
                raise ProtocolError("domain selection identity mismatch")
            return selection
        raise ProtocolError("no operation is selected for this slot")
