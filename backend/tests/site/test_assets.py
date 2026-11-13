import pytest
from tree_planner.site.repository import Repository, DomainError
from tree_planner.site.assets import AssetRegistry


def rights(status):
    return {
        x: status
        for x in ("local_use_status", "team_share_status", "public_display_status", "export_status")
    }


def test_registry_rights_digest_and_restart(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "asset.bin").write_bytes(b"synthetic")
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    info = registry.register(
        "asset.bin",
        source_reference="synthetic",
        licence_reference="unknown",
        evidence=["synthetic declaration"],
        capture_date="unknown",
        rights=rights("unknown"),
    )
    for purpose in rights("unknown"):
        with pytest.raises(DomainError):
            registry.read(info["registry_id"], purpose)
    permitted = registry.register(
        "asset.bin",
        source_reference="synthetic",
        licence_reference="declared",
        evidence=["declaration"],
        capture_date="unknown",
        rights=rights("permitted"),
    )
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    for purpose in rights("permitted"):
        assert registry.read(permitted["registry_id"], purpose) == b"synthetic"
    (root / "asset.bin").write_bytes(b"changed")
    with pytest.raises(DomainError):
        registry.read(permitted["registry_id"], "local_use_status")


@pytest.mark.parametrize(
    "path", ["../escape", "/absolute", "C:/escape", "https://example.com/a", "a\\b", "x/../y"]
)
def test_unsafe_paths(tmp_path, path):
    root = tmp_path / "bundle"
    root.mkdir()
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    with pytest.raises(DomainError):
        registry.register(
            path,
            source_reference="unknown",
            licence_reference="unknown",
            evidence=[],
            capture_date="unknown",
            rights=rights("unknown"),
        )


def test_symlink_escape(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"synthetic")
    try:
        (root / "link").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    with pytest.raises(DomainError):
        registry.register(
            "link",
            source_reference="unknown",
            licence_reference="unknown",
            evidence=[],
            capture_date="unknown",
            rights=rights("unknown"),
        )


@pytest.mark.parametrize("purpose", list(rights("restricted")))
def test_each_restricted_purpose_fails_closed(tmp_path, purpose):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "a").write_bytes(b"synthetic")
    permissions = rights("permitted")
    permissions[purpose] = "restricted"
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    item = registry.register(
        "a",
        source_reference="synthetic",
        licence_reference="declared",
        evidence=["declaration"],
        capture_date="unknown",
        rights=permissions,
    )
    with pytest.raises(DomainError):
        registry.read(item["registry_id"], purpose)


def test_missing_registry_id_and_missing_evidence(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "a").write_bytes(b"synthetic")
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    item = registry.register(
        "a",
        source_reference="synthetic",
        licence_reference="declared",
        evidence=[],
        capture_date="unknown",
        rights=rights("permitted"),
    )
    with pytest.raises(DomainError):
        registry.read(item["registry_id"], "local_use_status")
    with pytest.raises(DomainError):
        registry.read("../a", "local_use_status")


def test_symlink_substitution_at_use(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    asset = root / "a"
    asset.write_bytes(b"synthetic")
    outside = tmp_path / "outside"
    outside.write_bytes(b"synthetic")
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    item = registry.register(
        "a",
        source_reference="synthetic",
        licence_reference="declared",
        evidence=["declared"],
        capture_date="unknown",
        rights=rights("permitted"),
    )
    asset.unlink()
    try:
        asset.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(DomainError):
        registry.read(item["registry_id"], "local_use_status")


def test_source_registry_is_immutable_and_asset_binds_source(tmp_path):
    root = tmp_path / "bundle"
    root.mkdir()
    (root / "a").write_bytes(b"synthetic")
    registry = AssetRegistry(Repository(tmp_path / "db"), root)
    source = registry.register_source(
        source_reference="synthetic source",
        licence_reference="unknown",
        evidence=["declared"],
        rights=rights("permitted"),
    )
    asset = registry.register_from_source(
        "a", source_id=source["source_id"], capture_date="unknown"
    )
    source["rights"]["export_status"] = "restricted"
    reopened = AssetRegistry(Repository(tmp_path / "db"), root)
    assert reopened.get_source(asset["source_id"])["rights"]["export_status"] == "permitted"
    assert reopened.read(asset["registry_id"], "export_status") == b"synthetic"
    with pytest.raises(DomainError):
        reopened.register_from_source("a", source_id="missing", capture_date="unknown")
