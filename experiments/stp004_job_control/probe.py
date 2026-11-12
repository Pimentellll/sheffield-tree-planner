"""SQLite bookkeeping experiment; types and tokens are synthetic and non-canonical."""

import math
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from os import PathLike
from typing import Any

Record = dict[str, Any]


def _finite_time(value: object) -> bool:
    """Require finite values that survive SQLite REAL storage without rounding."""
    if type(value) not in (int, float):
        return False
    try:
        converted = float(value)
    except OverflowError:
        return False
    return math.isfinite(converted) and converted == value


SLOTS = {
    "evaluate_layout": "evaluation",
    "search_layouts": "search",
    "compare_locations": "comparison",
    "compare_scenarios": "comparison",
}
TERMINAL = {"completed", "failed", "cancelled"}


class ProbeError(Exception):
    """A safe, local bookkeeping rejection, not a production error envelope."""


class Store:
    """Own one connection; callers use a separate instance per thread."""

    def __init__(
        self, path: str | PathLike[str], capacity: int = 100, running_limit: int = 100
    ) -> None:
        if any(
            type(limit) is not int or limit < 1 for limit in (capacity, running_limit)
        ):
            raise ProbeError("limits must be positive integers")
        self.db = sqlite3.connect(path, isolation_level=None, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.capacity = capacity
        self.running_limit = running_limit
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
          job_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, operation TEXT NOT NULL,
          scenario TEXT NOT NULL, revision INTEGER NOT NULL, scope TEXT NOT NULL,
          fingerprint TEXT NOT NULL, payload TEXT NOT NULL, slot TEXT NOT NULL,
          selection_seq INTEGER NOT NULL, status TEXT NOT NULL, error TEXT,
          deadline REAL, run_id TEXT, source_job_id TEXT, mode TEXT,
          UNIQUE(operation, request_id));
        CREATE TABLE IF NOT EXISTS selections (
          scenario TEXT NOT NULL, revision INTEGER NOT NULL, scope TEXT NOT NULL,
          slot TEXT NOT NULL, seq INTEGER NOT NULL, job_id TEXT NOT NULL,
          PRIMARY KEY(scenario, revision, scope, slot));
        CREATE TABLE IF NOT EXISTS runs (
          run_id TEXT PRIMARY KEY, source_job_id TEXT NOT NULL, scenario TEXT NOT NULL,
          revision INTEGER NOT NULL, scope TEXT NOT NULL, operation TEXT NOT NULL,
          fingerprint TEXT NOT NULL, payload TEXT NOT NULL, token TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS history (
          id INTEGER PRIMARY KEY, job_id TEXT NOT NULL, event TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS active (singleton INTEGER PRIMARY KEY CHECK(singleton=1),
          scenario TEXT NOT NULL, revision INTEGER NOT NULL);
        """)

    @contextmanager
    def _write(self) -> Iterator[None]:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def close(self) -> None:
        """Close the owned connection."""
        self.db.close()

    def job(self, job_id: str) -> Record | None:
        """Return a detached job record, or None."""
        row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def history(self, job_id: str) -> list[str]:
        """Return ordered diagnostic events, including ignored late callbacks."""
        return [
            r[0]
            for r in self.db.execute(
                "SELECT event FROM history WHERE job_id=? ORDER BY id", (job_id,)
            )
        ]

    def run(self, run_id: str) -> Record | None:
        """Return an immutable synthetic run record, or None."""
        row = self.db.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return dict(row) if row else None

    def _event(self, job_id: str, event: str) -> None:
        self.db.execute(
            "INSERT INTO history(job_id,event) VALUES (?,?)", (job_id, event)
        )

    def accept(
        self,
        job_id: str,
        request_id: str,
        operation: str,
        scenario: str,
        revision: int,
        scope: str,
        fingerprint: str,
        payload: str,
        deadline: float | None = None,
    ) -> Record:
        """Atomically accept a synthetic request; identities are supplied upstream."""
        if (
            not isinstance(operation, str)
            or operation not in SLOTS
            or scope not in ("accepted", "hypothetical")
        ):
            raise ProbeError("invalid operation or scope")
        if (
            not all(
                isinstance(x, str) and x
                for x in (job_id, request_id, scenario, fingerprint, payload)
            )
            or type(revision) is not int
            or revision < 1
        ):
            raise ProbeError("invalid identity")
        if deadline is not None and not _finite_time(deadline):
            raise ProbeError("invalid deadline")
        deadline = float(deadline) if deadline is not None else None
        slot = SLOTS[operation]
        with self._write():
            prior = self.db.execute(
                "SELECT * FROM jobs WHERE operation=? AND request_id=?",
                (operation, request_id),
            ).fetchone()
            if prior:
                existing_id = self.job(job_id)
                if existing_id and existing_id["job_id"] != prior["job_id"]:
                    raise ProbeError("job ID conflict")
                if (
                    prior["scenario"],
                    prior["revision"],
                    prior["scope"],
                    prior["fingerprint"],
                    prior["payload"],
                    prior["deadline"],
                ) != (scenario, revision, scope, fingerprint, payload, deadline):
                    raise ProbeError("idempotency conflict")
                return dict(prior)
            if self.job(job_id):
                raise ProbeError("job ID conflict")
            count = self.db.execute(
                "SELECT count(*) FROM jobs WHERE status IN ('queued','running')"
            ).fetchone()[0]
            if count >= self.capacity:
                raise ProbeError("admission full")
            key = (scenario, revision, scope, slot)
            row = self.db.execute(
                "SELECT seq FROM selections WHERE scenario=? AND revision=? AND scope=? AND slot=?",
                key,
            ).fetchone()
            seq = row[0] + 1 if row else 1
            self.db.execute(
                """INSERT INTO jobs(job_id,request_id,operation,scenario,revision,scope,
                fingerprint,payload,slot,selection_seq,status,deadline) VALUES (?,?,?,?,?,?,?,?,?,?,'queued',?)""",
                (
                    job_id,
                    request_id,
                    operation,
                    scenario,
                    revision,
                    scope,
                    fingerprint,
                    payload,
                    slot,
                    seq,
                    deadline,
                ),
            )
            self.db.execute(
                """INSERT INTO selections VALUES (?,?,?,?,?,?) ON CONFLICT(scenario,revision,scope,slot)
                DO UPDATE SET seq=excluded.seq, job_id=excluded.job_id""",
                (*key, seq, job_id),
            )
            self._event(job_id, "queued")
            return self._require(job_id)

    def activate(self, scenario: str, revision: int) -> None:
        """Explicitly change the active accepted-scenario identity."""
        if (
            not isinstance(scenario, str)
            or not scenario
            or type(revision) is not int
            or revision < 1
        ):
            raise ProbeError("invalid active identity")
        with self._write():
            self.db.execute(
                "INSERT INTO active VALUES (1,?,?) ON CONFLICT(singleton) DO UPDATE SET scenario=excluded.scenario, revision=excluded.revision",
                (scenario, revision),
            )

    def current(
        self, scenario: str, revision: int, scope: str, slot: str
    ) -> Record | None:
        """Return the selected completed job only when its scope is current."""
        row = self.db.execute(
            """SELECT j.* FROM selections s JOIN jobs j ON j.job_id=s.job_id
            WHERE s.scenario=? AND s.revision=? AND s.scope=? AND s.slot=?
              AND j.status='completed' AND (s.scope!='accepted' OR EXISTS
                (SELECT 1 FROM active a WHERE a.singleton=1
                 AND a.scenario=s.scenario AND a.revision=s.revision))""",
            (scenario, revision, scope, slot),
        ).fetchone()
        return dict(row) if row else None

    def start(self, job_id: str) -> None:
        """Start a queued job subject to the bookkeeping running limit."""
        with self._write():
            job = self._require(job_id)
            if job["status"] != "queued":
                raise ProbeError("not queued")
            if (
                self.db.execute(
                    "SELECT count(*) FROM jobs WHERE status='running'"
                ).fetchone()[0]
                >= self.running_limit
            ):
                raise ProbeError("running full")
            self.db.execute(
                "UPDATE jobs SET status='running' WHERE job_id=?", (job_id,)
            )
            self._event(job_id, "running")

    def _require(self, job_id: str) -> Record:
        job = self.job(job_id)
        if job is None:
            raise ProbeError("unknown job")
        return job

    def _expire_if_due(self, job: Record, now: float | None) -> bool:
        """Reject clockless completion and persist expiry before publishing a result."""
        if job["deadline"] is None:
            return False
        if not _finite_time(now):
            raise ProbeError("finite clock required for deadline-bound delivery")
        if now < job["deadline"]:
            return False
        self.db.execute(
            "UPDATE jobs SET status='failed',error='DEADLINE_EXCEEDED' WHERE job_id=?",
            (job["job_id"],),
        )
        self._event(job["job_id"], "failed:DEADLINE_EXCEEDED")
        return True

    def finish(
        self,
        job_id: str,
        action: str,
        *,
        run_id: str | None = None,
        token: str | None = None,
        now: float | None = None,
    ) -> bool:
        """Apply a callback, preserving terminal states and recording late events."""
        if action not in ("complete", "fail", "cancel", "expire"):
            raise ProbeError("unknown callback")
        if now is not None and not _finite_time(now):
            raise ProbeError("invalid clock")
        with self._write():
            job = self._require(job_id)
            if job["status"] in TERMINAL:
                self._event(job_id, "late:" + action)
                return False
            if action == "complete" and self._expire_if_due(job, now):
                return True
            if action == "expire" and (
                now is None or job["deadline"] is None or now < job["deadline"]
            ):
                raise ProbeError("deadline not reached")
            if action == "complete":
                if (
                    job["status"] != "running"
                    or not isinstance(run_id, str)
                    or not run_id
                    or not isinstance(token, str)
                    or not token
                ):
                    raise ProbeError(
                        "completion requires running job and opaque run/token"
                    )
                try:
                    self.db.execute(
                        "INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            run_id,
                            job_id,
                            job["scenario"],
                            job["revision"],
                            job["scope"],
                            job["operation"],
                            job["fingerprint"],
                            job["payload"],
                            token,
                        ),
                    )
                except sqlite3.IntegrityError as exc:
                    raise ProbeError("run ID conflict") from exc
                self.db.execute(
                    "UPDATE jobs SET status='completed',run_id=?,source_job_id=?,mode='live' WHERE job_id=?",
                    (run_id, job_id, job_id),
                )
                state = "completed"
            else:
                state = "cancelled" if action == "cancel" else "failed"
                error = (
                    "DEADLINE_EXCEEDED"
                    if action == "expire"
                    else ("FAILED" if action == "fail" else None)
                )
                self.db.execute(
                    "UPDATE jobs SET status=?,error=? WHERE job_id=?",
                    (state, error, job_id),
                )
            self._event(job_id, state)
            return True

    def deliver_cached(
        self, job_id: str, run_id: str, *, now: float | None = None
    ) -> bool:
        """Bind a queued request to an identity-compatible immutable source run."""
        with self._write():
            job = self._require(job_id)
            run = self.run(run_id)
            if job["status"] != "queued" or not run:
                raise ProbeError("cache unavailable")
            if self._expire_if_due(job, now):
                return False
            fields = (
                "scenario",
                "revision",
                "scope",
                "operation",
                "fingerprint",
                "payload",
            )
            if any(job[f] != run[f] for f in fields):
                raise ProbeError("cache identity mismatch")
            self.db.execute(
                "UPDATE jobs SET status='running' WHERE job_id=?", (job_id,)
            )
            self._event(job_id, "running:cache")
            self.db.execute(
                "UPDATE jobs SET status='completed',run_id=?,source_job_id=?,mode='cached' WHERE job_id=?",
                (run_id, run["source_job_id"], job_id),
            )
            self._event(job_id, "completed:cached")
            return True

    def recover_exclusive_startup(self) -> int:
        """Fail abandoned running jobs; caller must ensure exclusive worker startup."""
        with self._write():
            ids = [
                r[0]
                for r in self.db.execute(
                    "SELECT job_id FROM jobs WHERE status='running'"
                )
            ]
            for job_id in ids:
                self.db.execute(
                    "UPDATE jobs SET status='failed',error='WORKER_INTERRUPTED' WHERE job_id=?",
                    (job_id,),
                )
                self._event(job_id, "failed:WORKER_INTERRUPTED")
            return len(ids)
