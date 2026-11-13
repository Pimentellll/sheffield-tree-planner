"""Local immutable snapshot storage. API dispatch must enforce actor permissions."""

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from tree_planner.canonical import canonical_bytes, content_hash


class DomainError(Exception):
    def __init__(self, code, message, retryable=False, details=None):
        super().__init__(message)
        self.code, self.message, self.retryable = code, message, retryable
        self.details = {} if details is None else details


class Repository:
    def __init__(self, workspace: Path):
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.db_path = self.workspace / "canopy.sqlite3"
        with self.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS snapshots (kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, scope TEXT NOT NULL, payload BLOB NOT NULL, hash TEXT NOT NULL, created TEXT NOT NULL, source BLOB, PRIMARY KEY(kind,id,revision))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS snapshot_source_integrity (kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, hash TEXT NOT NULL, PRIMARY KEY(kind,id,revision))"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS heads (kind TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL, PRIMARY KEY(kind,id))"
            )

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _ref(ref):
        if (
            type(ref) is not dict
            or set(ref) not in ({"kind", "id", "revision"}, {"kind", "id", "revision", "scope"})
            or type(ref.get("kind")) is not str
            or type(ref.get("id")) is not str
            or type(ref.get("revision")) is not int
            or not 0 < ref["revision"] <= 9223372036854775807
        ):
            raise DomainError("UNKNOWN_REVISION", "Invalid snapshot reference")
        return ref

    def _get(self, db, ref):
        ref = self._ref(ref)
        row = db.execute(
            "SELECT scope,payload,hash,created,source FROM snapshots WHERE kind=? AND id=? AND revision=?",
            (ref["kind"], ref["id"], ref["revision"]),
        ).fetchone()
        if row is None:
            raise DomainError("UNKNOWN_REVISION", "Snapshot revision is unresolved")
        scope, payload, digest, created, source = row
        if (scope and ref.get("scope") != scope) or (not scope and "scope" in ref):
            raise DomainError("REVISION_CONFLICT", "Snapshot scope mismatch")
        try:
            value = json.loads(payload)
            if canonical_bytes(value) != payload or content_hash(value) != digest:
                raise ValueError("snapshot integrity mismatch")
        except (ValueError, TypeError, UnicodeError) as exc:
            raise DomainError("REVISION_CONFLICT", "Snapshot integrity check failed") from exc
        if source is not None:
            try:
                source_value = json.loads(source)
                source_hash = db.execute(
                    "SELECT hash FROM snapshot_source_integrity WHERE kind=? AND id=? AND revision=?",
                    (ref["kind"], ref["id"], ref["revision"]),
                ).fetchone()
                if (
                    canonical_bytes(source_value) != source
                    or source_hash is None
                    or content_hash(source_value) != source_hash[0]
                ):
                    raise ValueError()
            except (ValueError, TypeError, UnicodeError) as exc:
                raise DomainError(
                    "REVISION_CONFLICT", "Snapshot source integrity check failed"
                ) from exc
        else:
            source_value = None
        actual_ref = {"kind": ref["kind"], "id": ref["id"], "revision": ref["revision"]}
        if scope:
            actual_ref["scope"] = scope
        return {
            "ref": actual_ref,
            "value": value,
            "content_hash": digest,
            "created_at_utc": created,
            "source_ref": source_value,
        }

    def head_reference(self, kind: str, identifier: str) -> dict:
        """Return explicit head metadata for authorisation, never a get fallback."""
        with self.transaction() as db:
            row = db.execute(
                "SELECT h.revision,s.scope FROM heads AS h JOIN snapshots AS s ON s.kind=h.kind AND s.id=h.id AND s.revision=h.revision WHERE h.kind=? AND h.id=?",
                (kind, identifier),
            ).fetchone()
            if row is None:
                raise DomainError("UNKNOWN_REVISION", "Snapshot head is unresolved")
            reference = {"kind": kind, "id": identifier, "revision": row[0]}
            if row[1]:
                reference["scope"] = row[1]
            return self._get(db, reference)["ref"]

    def get(self, reference):
        with self.transaction() as db:
            return self._get(db, reference)

    def _insert(self, db, kind, id_, revision, scope, value, source=None):
        try:
            payload = canonical_bytes(value)
            digest = content_hash(value)
            src = canonical_bytes(source) if source is not None else None
        except (ValueError, TypeError, OverflowError) as exc:
            raise DomainError("INVALID_INPUT", "Snapshot must contain finite JSON values") from exc
        created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        db.execute(
            "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?,?)",
            (kind, id_, revision, scope, payload, digest, created, src),
        )
        if source is not None:
            db.execute(
                "INSERT INTO snapshot_source_integrity VALUES (?,?,?,?)",
                (kind, id_, revision, content_hash(source)),
            )
        db.execute(
            "INSERT INTO heads VALUES (?,?,?) ON CONFLICT(kind,id) DO UPDATE SET revision=excluded.revision",
            (kind, id_, revision),
        )
        ref = {"kind": kind, "id": id_, "revision": revision}
        if scope:
            ref["scope"] = scope
        return self._get(db, ref)

    def create(self, kind, value):
        if kind not in ("site", "profile", "layout", "catalogue"):
            raise DomainError("INVALID_INPUT", "Unsupported snapshot kind")
        with self.transaction() as db:
            return self._insert(db, kind, uuid4().hex, 1, "", value)

    def replace(self, reference, value, *, if_match):
        with self.transaction() as db:
            old = self._get(db, reference)
            if reference["kind"] == "scenario":
                raise DomainError("INVALID_INPUT", "Use scenario preparation")
            head = db.execute(
                "SELECT revision FROM heads WHERE kind=? AND id=?",
                (reference["kind"], reference["id"]),
            ).fetchone()[0]
            if head != reference["revision"] or old["content_hash"] != if_match:
                raise DomainError("REVISION_CONFLICT", "Snapshot head or fingerprint changed")
            return self._insert(
                db, reference["kind"], reference["id"], head + 1, "", value, reference
            )

    def prepare_scenario(self, value, *, base_ref=None):
        with self.transaction() as db:
            if base_ref is not None:
                self._get(db, base_ref)
                if base_ref.get("kind") != "scenario" or base_ref.get("scope") != "accepted":
                    raise DomainError("REVISION_CONFLICT", "Base must be accepted")
            return self._insert(db, "scenario", uuid4().hex, 1, "hypothetical", value, base_ref)

    def accept_scenario(self, reference):
        """Human-only application boundary; never register this on the agent dispatcher."""
        with self.transaction() as db:
            item = self._get(db, reference)
            if reference["kind"] != "scenario" or reference.get("scope") != "hypothetical":
                raise DomainError("REVISION_CONFLICT", "Expected hypothetical scenario")
            head = db.execute(
                "SELECT revision FROM heads WHERE kind=? AND id=?", ("scenario", reference["id"])
            ).fetchone()[0]
            if head != reference["revision"]:
                raise DomainError("REVISION_CONFLICT", "Scenario head changed")
            return self._insert(
                db, "scenario", reference["id"], head + 1, "accepted", item["value"], reference
            )

    def agent(self):
        return _AgentRepository(self)


class _AgentRepository:
    def __init__(self, repository):
        self.__repository = repository

    def prepare_scenario(self, value, *, base_ref=None):
        return self.__repository.prepare_scenario(value, base_ref=base_ref)

    def get(self, reference):
        return self.__repository.get(reference)
