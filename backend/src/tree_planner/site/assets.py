"""Evidence-preserving local asset registry; declarations are not independent verification."""

from datetime import date
import hashlib
from pathlib import Path, PureWindowsPath
from uuid import uuid4

from .repository import DomainError
from tree_planner.canonical import canonical_bytes
import json

PURPOSES = ("local_use_status", "team_share_status", "public_display_status", "export_status")


class AssetRegistry:
    def __init__(self, repository, approved_root: Path):
        self.repository = repository
        root = Path(approved_root)
        try:
            if not root.is_absolute() or not root.is_dir():
                raise ValueError()
            self.root = root.resolve(strict=True)
            if root.absolute() != self.root:
                raise ValueError()
        except (OSError, ValueError, RuntimeError) as exc:
            raise DomainError(
                "INVALID_INPUT", "Approved root must be an existing direct directory"
            ) from exc
        with repository.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, root TEXT NOT NULL, metadata BLOB NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS asset_sources (id TEXT PRIMARY KEY, metadata BLOB NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS asset_integrity (kind TEXT NOT NULL, id TEXT NOT NULL, digest TEXT NOT NULL, PRIMARY KEY(kind,id))"
            )

    def _path(self, relative):
        if (
            type(relative) is not str
            or not relative
            or "\\" in relative
            or ":" in relative
            or PureWindowsPath(relative).is_absolute()
            or relative.startswith("/")
            or any(x in ("", ".", "..") for x in relative.split("/"))
            or any(ord(c) < 32 for c in relative)
        ):
            raise DomainError("INVALID_INPUT", "Unsafe asset path")
        if any(
            part.rstrip(" .").split(".")[0].upper()
            in {
                "CON",
                "PRN",
                "AUX",
                "NUL",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10)),
            }
            or part.endswith((" ", "."))
            for part in relative.split("/")
        ):
            raise DomainError("INVALID_INPUT", "Reserved asset path")
        try:
            if self.root.resolve(strict=True) != self.root or not self.root.is_dir():
                raise ValueError()
            path = self.root.joinpath(*relative.split("/"))
            # Refuse all links/reparse points, including links within the root.
            current = self.root
            for part in relative.split("/"):
                current = current / part
                stat = current.lstat()
                if current.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                    raise ValueError()
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(self.root) or not resolved.is_file():
                raise ValueError()
            return resolved
        except (OSError, ValueError, RuntimeError) as exc:
            raise DomainError("INVALID_INPUT", "Asset path is unavailable or unsafe") from exc

    def register(
        self,
        relative_path,
        *,
        source_reference,
        licence_reference,
        evidence,
        capture_date,
        rights,
        _source_id=None,
    ):
        if (
            type(source_reference) is not str
            or not source_reference
            or type(licence_reference) is not str
            or not licence_reference
            or type(evidence) is not list
            or any(type(x) is not str or not x for x in evidence)
            or type(rights) is not dict
            or set(rights) != set(PURPOSES)
            or any(v not in ("unknown", "restricted", "permitted") for v in rights.values())
        ):
            raise DomainError("INVALID_INPUT", "Invalid asset metadata")
        try:
            if capture_date != "unknown":
                date.fromisoformat(capture_date)
        except (ValueError, TypeError) as exc:
            raise DomainError("INVALID_INPUT", "Capture date must be ISO date or unknown") from exc
        if _source_id is not None:
            source = self.get_source(_source_id)
            if (
                source["source_reference"],
                source["licence_reference"],
                source["evidence"],
                source["rights"],
            ) != (source_reference, licence_reference, evidence, rights):
                raise DomainError("REVISION_CONFLICT", "Asset source metadata mismatch")
        path = self._path(relative_path)
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise DomainError("INVALID_INPUT", "Asset cannot be read") from exc
        metadata = {
            "registry_id": uuid4().hex,
            "relative_path": relative_path,
            "sha256": digest,
            "source_reference": source_reference,
            "licence_reference": licence_reference,
            "evidence": evidence,
            "capture_date": capture_date,
            "rights": rights,
            "verification": "supplier declaration; not independently verified",
            "source_id": _source_id,
        }
        with self.repository.transaction() as db:
            encoded = canonical_bytes(metadata)
            db.execute(
                "INSERT INTO assets VALUES (?,?,?)",
                (metadata["registry_id"], str(self.root), encoded),
            )
            db.execute(
                "INSERT INTO asset_integrity VALUES (?,?,?)",
                ("asset", metadata["registry_id"], hashlib.sha256(encoded).hexdigest()),
            )
        return json.loads(canonical_bytes(metadata))

    def register_source(self, *, source_reference, licence_reference, evidence, rights):
        if (
            type(source_reference) is not str
            or not source_reference
            or type(licence_reference) is not str
            or not licence_reference
            or type(evidence) is not list
            or any(type(x) is not str or not x for x in evidence)
            or type(rights) is not dict
            or set(rights) != set(PURPOSES)
            or any(v not in ("unknown", "restricted", "permitted") for v in rights.values())
        ):
            raise DomainError("INVALID_INPUT", "Invalid source metadata")
        source = {
            "source_id": uuid4().hex,
            "source_reference": source_reference,
            "licence_reference": licence_reference,
            "evidence": evidence,
            "rights": rights,
            "verification": "supplier declaration; not independently verified",
        }
        encoded = canonical_bytes(source)
        with self.repository.transaction() as db:
            db.execute("INSERT INTO asset_sources VALUES (?,?)", (source["source_id"], encoded))
            db.execute(
                "INSERT INTO asset_integrity VALUES (?,?,?)",
                ("source", source["source_id"], hashlib.sha256(encoded).hexdigest()),
            )
        return json.loads(encoded)

    def get_source(self, source_id):
        if type(source_id) is not str:
            raise DomainError("INVALID_INPUT", "Invalid source ID")
        with self.repository.transaction() as db:
            row = db.execute(
                "SELECT metadata FROM asset_sources WHERE id=?", (source_id,)
            ).fetchone()
            digest = db.execute(
                "SELECT digest FROM asset_integrity WHERE kind=? AND id=?", ("source", source_id)
            ).fetchone()
        if row is None:
            raise DomainError("UNKNOWN_REVISION", "Source is unresolved")
        return self._verified(row[0], digest)

    @staticmethod
    def _verified(payload, digest):
        try:
            data = json.loads(payload)
            if (
                not digest
                or canonical_bytes(data) != payload
                or hashlib.sha256(payload).hexdigest() != digest[0]
            ):
                raise ValueError()
            return data
        except (ValueError, TypeError, UnicodeError) as exc:
            raise DomainError("REVISION_CONFLICT", "Registry integrity check failed") from exc

    def register_from_source(self, relative_path, *, source_id, capture_date):
        source = self.get_source(source_id)
        # Store the source ID and a copy of the immutable rights evidence together.
        item = self.register(
            relative_path,
            source_reference=source["source_reference"],
            licence_reference=source["licence_reference"],
            evidence=source["evidence"],
            capture_date=capture_date,
            rights=source["rights"],
            _source_id=source_id,
        )
        return item

    def get(self, registry_id):
        if type(registry_id) is not str:
            raise DomainError("INVALID_INPUT", "Invalid registry ID")
        with self.repository.transaction() as db:
            row = db.execute(
                "SELECT metadata FROM assets WHERE id=? AND root=?", (registry_id, str(self.root))
            ).fetchone()
            digest = db.execute(
                "SELECT digest FROM asset_integrity WHERE kind=? AND id=?", ("asset", registry_id)
            ).fetchone()
        if row is None:
            raise DomainError("UNKNOWN_REVISION", "Asset is unresolved")
        return self._verified(row[0], digest)

    def read(self, registry_id, purpose):
        if purpose not in PURPOSES:
            raise DomainError("INVALID_INPUT", "Unknown rights purpose")
        item = self.get(registry_id)
        if item["rights"][purpose] != "permitted" or not item["evidence"]:
            raise DomainError("FORBIDDEN", "Asset use lacks evidenced permission")
        path = self._path(item["relative_path"])
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise DomainError("INVALID_INPUT", "Asset cannot be read") from exc
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise DomainError("REVISION_CONFLICT", "Asset content changed")
        return data
