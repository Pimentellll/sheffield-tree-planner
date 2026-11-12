"""Durable job selection and bounded, trusted in-process execution."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from tree_planner.canonical import canonical_bytes, content_hash
from tree_planner.contracts import (
    Job,
    JobRequest,
    Result,
    Selection,
    Scenario,
    ScenarioRef,
    Progress,
)
from tree_planner.contracts.operations import operation_slot

_MAX = 2**63 - 1
_locks_guard = threading.Lock()
_locks = {}


class JobStoreError(ValueError):
    pass


def _positive(value):
    if type(value) is not int or not 1 <= value <= _MAX:
        raise JobStoreError("positive SQLite integer required")
    return value


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _time(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise JobStoreError("UTC Z timestamp required")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise JobStoreError("invalid UTC timestamp") from exc


def _dump(value):
    return canonical_bytes(value).decode("utf-8")


def _error(code):
    messages = {
        "DEADLINE_EXCEEDED": "The job deadline expired.",
        "WORKER_INTERRUPTED": "The worker was interrupted.",
        "RESULT_VALIDATION_FAILED": "The result failed validation.",
        "NUMERICAL_FAILURE": "The operation failed.",
        "TOOL_UNAVAILABLE": "The operation is unavailable.",
        "CANCELLED": "The job was cancelled.",
    }
    if code not in messages:
        raise JobStoreError("unsupported failure code")
    return {
        "code": code,
        "message": messages[code],
        "retryable": code in {"WORKER_INTERRUPTED", "TOOL_UNAVAILABLE"},
        "field_errors": [],
        "details": {},
    }


def _snapshot(db, kind, digest):
    """Resolve only content named by admission, never by a result's narrative."""
    if (
        not digest
        or not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='snapshots'"
        ).fetchone()
    ):
        raise ValueError("admitted dependency unavailable")
    row = db.execute(
        "SELECT payload FROM snapshots WHERE kind=? AND hash=?", ("typed_" + kind, digest)
    ).fetchone()
    if row is None:
        raise ValueError("admitted dependency unavailable")
    value = json.loads(row[0])
    if content_hash(value) != digest:
        raise ValueError("admitted dependency corrupted")
    return value


def _validate_bindings(db, result, identity):
    """Bind nested identities at both live acceptance and stored-run trust boundaries."""
    scenario = Scenario.model_validate(identity["scenario"])
    ref = ScenarioRef(
        scenario_id=scenario.scenario_id, revision=scenario.revision, scope=scenario.scope
    )
    inp = scenario.input
    hashes = identity["content_hashes"]
    operation = identity["operation"]
    arguments = identity["arguments"]
    if result.input_snapshot_ref != ref:
        raise ValueError("result scenario mismatch")
    # Scenario comparison has no admitted two-scenario dependency graph yet.
    # Do not infer its contexts from result refs or pretend all scopes are equal.
    if operation == "compare_scenarios":
        raise ValueError("scenario comparison context unavailable")
    cases = {case.case_id: case for case in inp.evaluation_cases}
    original = None
    site = None
    for evaluated in result.layouts:
        if evaluated.scenario_ref != ref:
            raise ValueError("unadmitted layout scenario")
        layout = evaluated.layout.model_dump(mode="json")
        proposed = inp.proposed_layout_ref
        exact = (
            proposed is not None
            and (layout["layout_id"], layout["revision"]) == (proposed.layout_id, proposed.revision)
            and content_hash(layout) == hashes.get("layout")
        )
        if operation in ("evaluate_layout", "compare_locations"):
            if proposed is None or arguments["layout_ref"] != proposed.model_dump(mode="json"):
                raise ValueError("unadmitted requested layout")
            if exact:
                continue
            if operation == "evaluate_layout":
                raise ValueError("evaluated layout content mismatch")
            original = original or _snapshot(db, "layout", hashes.get("layout"))
            if (original["layout_id"], original["revision"]) != (
                proposed.layout_id,
                proposed.revision,
            ):
                raise ValueError("relocation source layout mismatch")
            moved = json.loads(_dump(original))
            placements = [
                p for p in moved["placements"] if p["placement_id"] == arguments["placement_id"]
            ]
            if len(placements) != 1:
                raise ValueError("unresolved moved placement")
            placements[0]["position_enu_m"] = arguments["alternative_position_enu_m"]
            # A counterfactual gets a distinct immutable layout identity, while
            # retaining the tree identity and every other placement field.
            if (
                layout["layout_id"] == original["layout_id"]
                or layout["kind"] != "hypothetical"
                or layout["placements"] != moved["placements"]
            ):
                raise ValueError("unrequested relocation changes")
        elif operation == "search_layouts":
            pins = {
                p.placement_id: p.model_dump(mode="json") for p in inp.constraints.pinned_placements
            }
            # A candidate-equivalent replacement is not the accepted pin. This
            # structural rule also protects legacy reads and cached deliveries.
            if not pins.keys() <= {p["placement_id"] for p in layout["placements"]}:
                raise ValueError("search omitted required pinned placement")
            if exact:
                continue
            if proposed is not None and layout["layout_id"] == proposed.layout_id:
                raise ValueError("search rewrote admitted layout identity")
            site = site or _snapshot(db, "site", hashes.get("site"))
            if (
                site["site_id"],
                site["scene_revision"],
                site["semantic_revision"],
                site["candidate_catalogue_fingerprint"],
            ) != (
                inp.site_id,
                inp.scene_revision,
                inp.semantic_revision,
                inp.candidate_catalogue_fingerprint,
            ):
                raise ValueError("search site identity mismatch")
            candidates = {c["candidate_id"]: c for c in site["candidate_catalogue"]}
            for placement in layout["placements"]:
                if placement["placement_id"] in pins:
                    if placement != pins[placement["placement_id"]]:
                        raise ValueError("search changed pinned placement")
                else:
                    candidate = candidates.get(placement["candidate_id"])
                    if (
                        candidate is None
                        or placement["pinned"]
                        or placement["profile_id"] not in inp.constraints.allowed_profile_ids
                        or any(
                            placement[k] != candidate[k]
                            for k in ("location_id", "profile_id", "position_enu_m")
                        )
                    ):
                        raise ValueError("unadmitted search placement")
                profile = _snapshot(db, "profile", hashes.get("profile:" + placement["profile_id"]))
                if (
                    profile["profile_id"] != placement["profile_id"]
                    or profile["library_revision"] != inp.profile_library_revision
                    or any(
                        profile["states"][case.profile_state]["horizon_years"] != case.horizon_years
                        for case in inp.evaluation_cases
                    )
                ):
                    raise ValueError("search profile identity mismatch")
        else:
            raise ValueError("unsupported result operation")
    for item in (*result.metrics, *result.missing_metrics, *result.constraints):
        if item.scenario_ref != ref:
            raise ValueError("unadmitted result item scenario")
        if item.case_id is None:  # Layout-wide constraints have no case.
            continue
        case = cases.get(item.case_id)
        if case is None:
            raise ValueError("unadmitted result case")
        if hasattr(item, "horizon_years"):
            if item.horizon_years != case.horizon_years:
                raise ValueError("result horizon mismatch")
            if item.target_id is not None and item.target_id not in case.target_ids:
                raise ValueError("unadmitted metric target")
    if result.source_ids:
        # Rebuild the admitted source manifest from its hashed input graph.
        # Result-provided IDs never select registry rows or authorize themselves.
        site = site or _snapshot(db, "site", hashes.get("site"))
        graph = [identity["scenario"], site]
        graph.extend(
            _snapshot(db, "profile", digest)
            for key, digest in hashes.items()
            if key.startswith("profile:")
        )
        source_ids = set()

        def collect(value):
            if isinstance(value, dict):
                source_ids.update(value.get("source_ids", []))
                if value.get("source_id") is not None:
                    source_ids.add(value["source_id"])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(graph)
        if not db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='asset_sources'"
        ).fetchone():
            raise ValueError("source context unavailable")
        sources = {}
        for source_id in source_ids:
            row = db.execute(
                "SELECT metadata FROM asset_sources WHERE id=?", (source_id,)
            ).fetchone()
            if row is None:
                raise ValueError("source context unavailable")
            sources[source_id] = json.loads(row[0])
        if (
            content_hash(sources) != hashes.get("sources")
            or not set(result.source_ids) <= sources.keys()
        ):
            raise ValueError("unadmitted result sources")


class JobStore:
    def __init__(self, db_path: Path, *, capacity: int = 64):
        self.db_path = Path(db_path).resolve()
        self.capacity = _positive(capacity)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with _locks_guard:
            self._execution_lock = _locks.setdefault(str(self.db_path), threading.Lock())
        self._events = {}
        self._events_lock = threading.Lock()
        db = self._connect()
        try:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS job_records (job_id TEXT PRIMARY KEY, operation TEXT NOT NULL, request_id TEXT NOT NULL, request_json TEXT NOT NULL, identity_json TEXT NOT NULL, deadline TEXT NOT NULL, reserved_run_id TEXT NOT NULL, data TEXT NOT NULL, UNIQUE(operation,request_id));
            CREATE TABLE IF NOT EXISTS job_selections (scenario_id TEXT NOT NULL, revision INTEGER NOT NULL, scope TEXT NOT NULL, slot TEXT NOT NULL, seq INTEGER NOT NULL, job_id TEXT NOT NULL, PRIMARY KEY(scenario_id,revision,scope,slot));
            CREATE TABLE IF NOT EXISTS job_active (singleton INTEGER PRIMARY KEY CHECK(singleton=1), scenario_id TEXT NOT NULL, revision INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS job_invalidations (job_id TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS job_runs (run_id TEXT PRIMARY KEY, identity_json TEXT NOT NULL, result_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS job_events (id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, event TEXT NOT NULL, at_utc TEXT NOT NULL);
            """)
        finally:
            db.close()

    def _connect(self):
        db = sqlite3.connect(str(self.db_path), timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=30000")
        return db

    @contextmanager
    def _write(self, connection=None):
        if connection is not None:
            if not connection.in_transaction:
                raise JobStoreError("caller connection must have an active transaction")
            database = connection.execute("PRAGMA database_list").fetchone()[2]
            if not database or Path(database).resolve() != self.db_path:
                raise JobStoreError("caller connection must use the jobs database")
            previous_factory = connection.row_factory
            try:
                yield connection
            finally:
                connection.row_factory = previous_factory
            return
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _read(self, sql, args=()):
        db = self._connect()
        try:
            return db.execute(sql, args).fetchone()
        finally:
            db.close()

    def _row(self, db, job_id):
        row = db.execute("SELECT * FROM job_records WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise JobStoreError("unknown job")
        return row

    def _save(self, db, data, event):
        model = Job.model_validate(data)
        db.execute(
            "UPDATE job_records SET data=? WHERE job_id=?",
            (_dump(model.model_dump(mode="json")), model.job_id),
        )
        db.execute(
            "INSERT INTO job_events(job_id,event,at_utc) VALUES (?,?,?)",
            (model.job_id, event, _now()),
        )
        return model

    def get_job(self, job_id):
        row = self._read("SELECT data FROM job_records WHERE job_id=?", (job_id,))
        return Job.model_validate_json(row[0]) if row else None

    def submit(self, request, scenario, *, content_hashes, deadline_utc, connection=None):
        request = JobRequest.model_validate(request).model_dump(mode="json")
        scenario = Scenario.model_validate(scenario).model_dump(mode="json")
        ref = request["scenario_ref"]
        _positive(ref["revision"])
        if (scenario["scenario_id"], scenario["revision"], scenario["scope"]) != (
            ref["scenario_id"],
            ref["revision"],
            ref["scope"],
        ):
            raise JobStoreError("scenario snapshot identity mismatch")
        if _time(deadline_utc) > _time(scenario["input"]["search"]["deadline_utc"]):
            raise JobStoreError("deadline exceeds scenario deadline")
        # Include the complete snapshot and all supplied resolved dependencies. Caller owns resolution.
        if (
            not isinstance(content_hashes, dict)
            or not content_hashes
            or any(
                not isinstance(k, str)
                or not k
                or not isinstance(v, str)
                or len(v) != 64
                or any(c not in "0123456789abcdef" for c in v)
                for k, v in content_hashes.items()
            )
        ):
            raise JobStoreError("resolved content hashes required")
        identity = {
            "scenario": scenario,
            "content_hashes": content_hashes,
            "operation": request["operation"],
            "arguments": request["arguments"],
        }
        identity_json = _dump(identity)
        request_json = _dump(
            {"request": request, "identity": identity, "deadline_utc": deadline_utc}
        )
        fingerprint = content_hash(identity)
        slot = operation_slot(request["operation"])
        with self._write(connection) as db:
            db.row_factory = sqlite3.Row
            old = db.execute(
                "SELECT * FROM job_records WHERE operation=? AND request_id=?",
                (request["operation"], request["request_id"]),
            ).fetchone()
            if old:
                if old["request_json"] != request_json:
                    raise JobStoreError("idempotency conflict")
                return Job.model_validate_json(old["data"])
            if (
                db.execute(
                    "SELECT count(*) FROM job_records WHERE json_extract(data,'$.status') IN ('queued','running')"
                ).fetchone()[0]
                >= self.capacity
            ):
                raise JobStoreError("admission capacity reached")
            key = (ref["scenario_id"], ref["revision"], ref["scope"], slot)
            selected = db.execute(
                "SELECT seq FROM job_selections WHERE scenario_id=? AND revision=? AND scope=? AND slot=?",
                key,
            ).fetchone()
            seq = _positive((selected[0] if selected else 0) + 1)
            job_id = uuid.uuid4().hex
            data = {
                "schema_version": "0.1.0",
                "job_id": job_id,
                "request_id": request["request_id"],
                "operation": request["operation"],
                "scenario_id": ref["scenario_id"],
                "scenario_revision": ref["revision"],
                "scope": ref["scope"],
                "input_fingerprint": fingerprint,
                "view_slot": slot,
                "selection_seq": seq,
                "status": "queued",
                "run_id": None,
                "delivery": None,
                "progress": None,
                "created_at_utc": _now(),
                "started_at_utc": None,
                "finished_at_utc": None,
                "error": None,
                "cancel_requested": False,
                "superseded_by_revision": None,
            }
            job = Job.model_validate(data)
            db.execute(
                "INSERT INTO job_records VALUES (?,?,?,?,?,?,?,?)",
                (
                    job_id,
                    request["operation"],
                    request["request_id"],
                    request_json,
                    identity_json,
                    deadline_utc,
                    uuid.uuid4().hex,
                    _dump(data),
                ),
            )
            db.execute(
                "INSERT INTO job_selections VALUES (?,?,?,?,?,?) ON CONFLICT(scenario_id,revision,scope,slot) DO UPDATE SET seq=excluded.seq,job_id=excluded.job_id",
                (*key, seq, job_id),
            )
            db.execute(
                "INSERT INTO job_events(job_id,event,at_utc) VALUES (?,?,?)",
                (job_id, "queued", _now()),
            )
            return job

    accept = submit

    def activate(self, scenario_id, revision, *, connection=None):
        _positive(revision)
        if not isinstance(scenario_id, str) or not scenario_id:
            raise JobStoreError("scenario id required")
        with self._write(connection) as db:
            db.row_factory = sqlite3.Row
            active = db.execute(
                "SELECT scenario_id,revision FROM job_active WHERE singleton=1"
            ).fetchone()
            if active is not None and tuple(active) == (scenario_id, revision):
                return
            db.execute(
                "INSERT OR IGNORE INTO job_invalidations(job_id) SELECT job_id FROM job_records WHERE json_extract(data,'$.scope')='accepted'"
            )
            db.execute(
                "INSERT INTO job_active VALUES (1,?,?) ON CONFLICT(singleton) DO UPDATE SET scenario_id=excluded.scenario_id,revision=excluded.revision",
                (scenario_id, revision),
            )
            for row in db.execute(
                "SELECT data FROM job_records WHERE json_extract(data,'$.scope')='accepted'"
            ).fetchall():
                data = json.loads(row[0])
                if (
                    data["scenario_id"] == scenario_id
                    and data["scenario_revision"] < revision
                    and data["superseded_by_revision"] is None
                ):
                    data["superseded_by_revision"] = revision
                    self._save(db, data, "superseded")

    def active_ref(self) -> ScenarioRef | None:
        row = self._read("SELECT scenario_id,revision FROM job_active WHERE singleton=1")
        return ScenarioRef(scenario_id=row[0], revision=row[1], scope="accepted") if row else None

    def selection(self, scenario_id, revision, scope, slot):
        _positive(revision)
        row = self._read(
            "SELECT seq,job_id FROM job_selections WHERE scenario_id=? AND revision=? AND scope=? AND slot=?",
            (scenario_id, revision, scope, slot),
        )
        return (
            Selection.model_validate(
                {
                    "scenario_ref": {
                        "scenario_id": scenario_id,
                        "revision": revision,
                        "scope": scope,
                    },
                    "view_slot": slot,
                    "selection_seq": row[0],
                    "accepted_job_id": row[1],
                }
            )
            if row
            else None
        )

    def current(self, scenario_id, revision, scope, slot):
        _positive(revision)
        row = self._read(
            """SELECT r.data FROM job_selections s
            JOIN job_records r ON r.job_id=s.job_id
            WHERE s.scenario_id=? AND s.revision=? AND s.scope=? AND s.slot=?
            AND (s.scope != 'accepted' OR (EXISTS
                (SELECT 1 FROM job_active a WHERE a.singleton=1 AND a.scenario_id=s.scenario_id AND a.revision=s.revision)
                AND NOT EXISTS (SELECT 1 FROM job_invalidations i WHERE i.job_id=r.job_id)))""",
            (scenario_id, revision, scope, slot),
        )
        if not row:
            return None
        job = Job.model_validate_json(row[0])
        if job.status != "completed" or job.superseded_by_revision is not None:
            return None
        # Old completed rows are not trusted merely because selection still points
        # at them. read_run also verifies their original source-job/run binding.
        result = self.read_run(job.run_id)
        if result is None or (
            result.source_job_id,
            result.input_snapshot_ref,
            result.input_fingerprint,
        ) != (
            job.delivery.source_job_id,
            ScenarioRef(
                scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
            ),
            job.input_fingerprint,
        ):
            raise JobStoreError("current result identity mismatch")
        return job

    def _terminal(self, db, row, code, *, cancel=False):
        data = json.loads(row["data"])
        if data["status"] in ("completed", "failed", "cancelled"):
            db.execute(
                "INSERT INTO job_events(job_id,event,at_utc) VALUES (?,?,?)",
                (data["job_id"], "late:" + code, _now()),
            )
            return False
        data.update(
            status="cancelled" if cancel else "failed",
            finished_at_utc=_now(),
            error=_error(code),
            cancel_requested=cancel or data["cancel_requested"],
        )
        self._save(db, data, code)
        return True

    def cancel(self, job_id):
        with self._write() as db:
            row = self._row(db, job_id)
            if json.loads(row["data"])["status"] not in (
                "completed",
                "failed",
                "cancelled",
            ) and _time(_now()) >= _time(row["deadline"]):
                changed = self._terminal(db, row, "DEADLINE_EXCEEDED")
            else:
                changed = self._terminal(db, row, "CANCELLED", cancel=True)
        with self._events_lock:
            event = self._events.get(job_id)
            if event:
                event.set()
        return changed

    def fail(self, job_id, code="NUMERICAL_FAILURE"):
        if code == "CANCELLED":
            raise JobStoreError("use cancel")
        with self._write() as db:
            row = self._row(db, job_id)
            if json.loads(row["data"])["status"] not in (
                "completed",
                "failed",
                "cancelled",
            ) and _time(_now()) >= _time(row["deadline"]):
                code = "DEADLINE_EXCEEDED"
            return self._terminal(db, row, code)

    def expire(self, job_id):
        with self._write() as db:
            row = self._row(db, job_id)
            if _time(_now()) < _time(row["deadline"]):
                return False
            return self._terminal(db, row, "DEADLINE_EXCEEDED")

    def claim(self):
        with self._write() as db:
            # Running database records never exceed the one-worker capacity.
            if db.execute(
                "SELECT 1 FROM job_records WHERE json_extract(data,'$.status')='running' LIMIT 1"
            ).fetchone():
                return None
            rows = db.execute(
                "SELECT * FROM job_records WHERE json_extract(data,'$.status')='queued' ORDER BY rowid"
            ).fetchall()
            for row in rows:
                if _time(_now()) >= _time(row["deadline"]):
                    self._terminal(db, row, "DEADLINE_EXCEEDED")
                    continue
                data = json.loads(row["data"])
                data.update(status="running", started_at_utc=_now())
                return self._save(db, data, "running")
        return None

    def complete(self, job_id, result):
        with self._write() as db:
            row = self._row(db, job_id)
            data = json.loads(row["data"])
            if data["status"] in ("completed", "failed", "cancelled"):
                self._terminal(db, row, "RESULT_VALIDATION_FAILED")
                return False
            if _time(_now()) >= _time(row["deadline"]):
                self._terminal(db, row, "DEADLINE_EXCEEDED")
                return False
            if data["status"] != "running":
                raise JobStoreError("completion requires running job")
            try:
                if isinstance(result, Result):
                    result = result.model_dump(mode="json")
                result = Result.model_validate_json(_dump(result))
                raw = result.model_dump(mode="json")
                original = json.loads(row["request_json"])["request"]
                identity = json.loads(row["identity_json"])
                settings = identity["scenario"]["input"]
                provenance = raw["provenance"]
                if (
                    result.run_id != row["reserved_run_id"]
                    or provenance["evaluator_version"] != settings["numerics"]["evaluator_version"]
                    or provenance["solar_version"] != settings["numerics"]["solar_version"]
                    or provenance["search_version"] != settings["search"]["version"]
                    or provenance["seed"] != settings["search"]["seed"]
                    or provenance["source_hashes"] != identity["content_hashes"]
                    or result.source_job_id != job_id
                    or result.scenario_id != data["scenario_id"]
                    or result.scenario_revision != data["scenario_revision"]
                    or result.scope != data["scope"]
                    or result.input_fingerprint != data["input_fingerprint"]
                    or raw["operation"] != original["operation"]
                    or raw["arguments"] != original["arguments"]
                ):
                    raise ValueError("result identity mismatch")
                _validate_bindings(db, result, identity)
                encoded = _dump(raw)
                if _time(_now()) >= _time(row["deadline"]):
                    self._terminal(db, row, "DEADLINE_EXCEEDED")
                    return False
                db.execute(
                    "INSERT INTO job_runs VALUES (?,?,?)",
                    (result.run_id, row["identity_json"], encoded),
                )
                if _time(_now()) >= _time(row["deadline"]):
                    db.execute("DELETE FROM job_runs WHERE run_id=?", (result.run_id,))
                    self._terminal(db, row, "DEADLINE_EXCEEDED")
                    return False
            except (ValueError, TypeError, KeyError, sqlite3.IntegrityError):
                self._terminal(db, row, "RESULT_VALIDATION_FAILED")
                return False
            self._deliver(db, data, result, "live")
            return True

    def _deliver(self, db, data, result, mode):
        stamp = _now()
        delivery = {
            "job_id": data["job_id"],
            "run_id": result.run_id,
            "source_job_id": result.source_job_id,
            "scenario_id": data["scenario_id"],
            "scenario_revision": data["scenario_revision"],
            "scope": data["scope"],
            "input_fingerprint": data["input_fingerprint"],
            "view_slot": data["view_slot"],
            "selection_seq": data["selection_seq"],
            "execution_mode": mode,
            "delivered_at_utc": stamp,
        }
        data.update(
            status="completed",
            started_at_utc=data["started_at_utc"] or stamp,
            finished_at_utc=stamp,
            run_id=result.run_id,
            delivery=delivery,
        )
        self._save(db, data, "completed:" + mode)

    def _validated_run(self, db, run):
        try:
            result = Result.model_validate_json(run["result_json"])
            source = self._row(db, result.source_job_id)
            source_job = Job.model_validate_json(source["data"])
            identity = json.loads(run["identity_json"])
            request = json.loads(source["request_json"])["request"]
            settings = identity["scenario"]["input"]
            raw = result.model_dump(mode="json")
            p = raw["provenance"]
            if (
                run["run_id"] != result.run_id
                or source["reserved_run_id"] != result.run_id
                or source["identity_json"] != run["identity_json"]
                or source_job.status != "completed"
                or source_job.run_id != result.run_id
                or source_job.job_id != result.source_job_id
                or result.input_fingerprint != content_hash(identity)
                or (result.scenario_id, result.scenario_revision, result.scope)
                != (source_job.scenario_id, source_job.scenario_revision, source_job.scope)
                or raw["operation"] != request["operation"]
                or raw["arguments"] != request["arguments"]
                or p["evaluator_version"] != settings["numerics"]["evaluator_version"]
                or p["solar_version"] != settings["numerics"]["solar_version"]
                or p["search_version"] != settings["search"]["version"]
                or p["seed"] != settings["search"]["seed"]
                or p["source_hashes"] != identity["content_hashes"]
            ):
                raise ValueError("run identity mismatch")
            _validate_bindings(db, result, identity)
            return result
        except (ValueError, TypeError, KeyError) as exc:
            raise JobStoreError("stored result failed validation") from exc

    def deliver_cached(self, job_id, run_id):
        with self._write() as db:
            row = self._row(db, job_id)
            data = json.loads(row["data"])
            if data["status"] != "queued":
                raise JobStoreError("cache requires queued job")
            if _time(_now()) >= _time(row["deadline"]):
                self._terminal(db, row, "DEADLINE_EXCEEDED")
                return False
            run = db.execute("SELECT * FROM job_runs WHERE run_id=?", (run_id,)).fetchone()
            if not run or run["identity_json"] != row["identity_json"]:
                raise JobStoreError("cache identity mismatch")
            try:
                result = self._validated_run(db, run)
            except JobStoreError:
                self._terminal(db, row, "RESULT_VALIDATION_FAILED")
                return False
            if _time(_now()) >= _time(row["deadline"]):
                self._terminal(db, row, "DEADLINE_EXCEEDED")
                return False
            self._deliver(db, data, result, "cached")
            return True

    def read_run(self, run_id):
        db = self._connect()
        try:
            run = db.execute("SELECT * FROM job_runs WHERE run_id=?", (run_id,)).fetchone()
            return self._validated_run(db, run) if run else None
        finally:
            db.close()

    def update_progress(self, job_id, progress):
        progress = Progress.model_validate(progress).model_dump(mode="json")
        with self._write() as db:
            row = self._row(db, job_id)
            data = json.loads(row["data"])
            if data["status"] != "running":
                return False
            if _time(_now()) >= _time(row["deadline"]):
                self._terminal(db, row, "DEADLINE_EXCEEDED")
                return False
            data["progress"] = progress
            self._save(db, data, "progress")
            return True

    def recover_exclusive_startup(self, *, exclusive=False):
        if exclusive is not True:
            raise JobStoreError("exclusive worker ownership required")
        if self._execution_lock.locked():
            raise JobStoreError("local worker is still executing")
        with self._write() as db:
            rows = db.execute(
                "SELECT * FROM job_records WHERE json_extract(data,'$.status')='running'"
            ).fetchall()
            for row in rows:
                self._terminal(db, row, "WORKER_INTERRUPTED")
            return len(rows)

    def run_one(self, handlers, stop_event):
        """Run one trusted handler synchronously; never runs two calls per process/database."""
        if not self._execution_lock.acquire(blocking=False):
            return None
        try:
            if stop_event.is_set():
                return None
            job = self.claim()
            if job is None:
                return None
            local_stop = threading.Event()
            with self._events_lock:
                self._events[job.job_id] = local_stop
            row = self._read("SELECT * FROM job_records WHERE job_id=?", (job.job_id,))
            watcher_done = threading.Event()

            def watchdog():
                while not watcher_done.is_set():
                    remaining = (_time(row["deadline"]) - _time(_now())).total_seconds()
                    if remaining <= 0:
                        local_stop.set()
                        self.expire(job.job_id)
                        return
                    if stop_event.is_set():
                        local_stop.set()
                    watcher_done.wait(min(remaining, 0.1))

            watcher = threading.Thread(target=watchdog, name="tree-planner-deadline", daemon=True)
            watcher.start()
            try:
                handler = handlers.get(job.operation)
                if handler is None:
                    self.fail(job.job_id, "TOOL_UNAVAILABLE")
                else:
                    try:
                        result = handler(
                            job,
                            json.loads(row["request_json"]),
                            row["reserved_run_id"],
                            local_stop,
                            stop_event,
                        )
                        self.complete(job.job_id, result)
                    except Exception:
                        self.fail(job.job_id, "NUMERICAL_FAILURE")
            finally:
                watcher_done.set()
                watcher.join()
                with self._events_lock:
                    self._events.pop(job.job_id, None)
            return self.get_job(job.job_id)
        finally:
            self._execution_lock.release()


class JobWorker:
    """One polling worker; stopping cannot forcibly terminate a handler thread."""

    def __init__(self, store, handlers, *, poll_interval=0.1):
        if poll_interval <= 0:
            raise ValueError("positive poll interval required")
        self.store, self.handlers, self.poll_interval = store, dict(handlers), poll_interval
        self.stop_event = threading.Event()
        self._thread = None

    def start(self, *, exclusive=False):
        if self._thread is not None and self._thread.is_alive():
            raise JobStoreError("worker already started")
        if exclusive is not True:
            raise JobStoreError("exclusive worker ownership required")
        self.store.recover_exclusive_startup(exclusive=True)
        self.stop_event.clear()

        def loop():
            while not self.stop_event.is_set():
                if self.store.run_one(self.handlers, self.stop_event) is None:
                    self.stop_event.wait(self.poll_interval)

        self._thread = threading.Thread(target=loop, name="tree-planner-jobs", daemon=True)
        self._thread.start()

    def stop(self, timeout=None):
        self.stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout)
        return self._thread is None or not self._thread.is_alive()
