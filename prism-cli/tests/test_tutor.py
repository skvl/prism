import os
import shutil
import tempfile

import pytest
from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.vault.vault import Vault
from prism_cli.tutor import Tutor


@pytest.fixture
def vault_dir():
    d = tempfile.mkdtemp()
    Vault.init(d)
    types_dir = os.path.join(d, ".metadata", "types")
    from prism.types.builtins import BOOKMARK_TOML, CONTACT_TOML, FILE_TOML, NOTE_TOML, PATH_TOML

    for fname, content in [
        ("note.toml", NOTE_TOML),
        ("contact.toml", CONTACT_TOML),
        ("bookmark.toml", BOOKMARK_TOML),
        ("file.toml", FILE_TOML),
        ("path.toml", PATH_TOML),
    ]:
        with open(os.path.join(types_dir, fname), "w") as f:
            f.write(content)
    yield d
    shutil.rmtree(d)


@pytest.fixture
def vault(vault_dir):
    return Vault.open(vault_dir)


@pytest.fixture
def tutor(vault):
    t = Tutor()
    t.vault = vault
    return t


# ── Verify Vault Init ───────────────────────────────────────────────────


class TestVerifyVaultInit:
    def test_initialized(self, vault):
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_vault_init(vault) is True

    def test_not_initialized(self):
        tmp = tempfile.mkdtemp()
        try:
            vault = Vault(tmp, vault_uuid="test", schema_version=1, created_at="2024-01-01")
            tutor = Tutor()
            tutor.vault = vault
            assert tutor._verify_vault_init(vault) is False
        finally:
            shutil.rmtree(tmp)


# ── Verify Node Count ───────────────────────────────────────────────────


class TestVerifyNodeCount:
    def test_matching_count(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Note 1")
        manager.create_node(type_name="note", title="Note 2")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_node_count(vault, 2, "note") is True

    def test_non_matching_type(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Note 1")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_node_count(vault, 0, "contact") is True


# ── Verify Node Has Tag ────────────────────────────────────────────────


class TestVerifyNodeHasTag:
    def test_tag_present(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tagged", tags=["work"])
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_node_has_tag(vault, meta.uuid, "work") is True

    def test_tag_absent(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="No Tag")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_node_has_tag(vault, meta.uuid, "work") is False


# ── Verify Link Exists ─────────────────────────────────────────────────


class TestVerifyLinkExists:
    def test_link_exists(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        storage_dir = compute_storage_path(vault.path, source.uuid)
        source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        source_meta.links = [{"target": target.uuid}]
        source_meta.save(NodeMetadata.metadata_path(storage_dir))
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_link_exists(vault, source.uuid, target.uuid) is True

    def test_link_not_exists(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_link_exists(vault, source.uuid, target.uuid) is False


# ── Verify Backlink ────────────────────────────────────────────────────


class TestVerifyBacklink:
    def test_backlink_found(self, vault):
        manager = NodeManager(vault.path)
        target = manager.create_node(type_name="note", title="Target")
        source = manager.create_node(type_name="note", title="Source")
        storage_dir = compute_storage_path(vault.path, source.uuid)
        source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        source_meta.links = [{"target": target.uuid}]
        source_meta.save(NodeMetadata.metadata_path(storage_dir))
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_backlink(vault, target.uuid, source.uuid) is True


# ── Verify Query Result ────────────────────────────────────────────────


class TestVerifyQueryResult:
    def test_query_finds_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Query Me", tags=["test"])
        tutor = Tutor()
        tutor.vault = vault
        tutor._fmt = {"_full_" + meta.uuid[:12]: meta.uuid}
        assert tutor._verify_query_result(vault, "tag:test", meta.uuid[:12]) is True


# ── Verify File Imported ───────────────────────────────────────────────


class TestVerifyFileImported:
    def test_file_imported(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "import_me.txt")
        with open(file_path, "w") as f:
            f.write("tutor import test")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="file", title="test.txt", blob_path=file_path)
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_file_imported(vault, meta.blob_sha256) is True

    def test_file_not_imported(self, vault):
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_file_imported(vault, "nonexistent_hash") is False


# ── Verify Blob Integrity ──────────────────────────────────────────────


class TestVerifyBlobIntegrity:
    def test_valid_blob(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "valid.txt")
        with open(file_path, "w") as f:
            f.write("valid content")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Valid", blob_path=file_path)
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_blob_integrity(vault, meta.uuid) is True

    def test_corrupted_blob(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Corrupted")
        storage_dir = compute_storage_path(vault.path, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_obj = NodeMetadata.from_toml(meta_path)
        meta_obj.blob_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        meta_obj.save(meta_path)
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_blob_integrity(vault, meta.uuid) is False


# ── Verify Change Detected ─────────────────────────────────────────────


class TestVerifyChangeDetected:
    def test_change_detected(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Changed")
        storage_dir = compute_storage_path(vault.path, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_obj = NodeMetadata.from_toml(meta_path)
        meta_obj.blob_mtime = "0"
        meta_obj.save(meta_path)
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_change_detected(vault) is True

    def test_clean_no_change(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Clean")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_change_detected(vault) is False


# ── Verify Tag Count ───────────────────────────────────────────────────


class TestVerifyTagCount:
    def test_meets_threshold(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work", "personal"])
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_tag_count(vault, 2) is True

    def test_below_threshold(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_tag_count(vault, 5) is False


# ── Verify Tag Renamed ─────────────────────────────────────────────────


class TestVerifyTagRenamed:
    def test_tag_renamed(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        manager.rename_tag("work", "tasks")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_tag_renamed(vault, "work", "tasks") is True

    def test_tag_not_renamed(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_tag_renamed(vault, "work", "tasks") is False


# ── Verify Always True ─────────────────────────────────────────────────


class TestVerifyAlwaysTrue:
    def test_always_true(self, vault):
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_always_true(vault) is True


# ── Capture UUID ───────────────────────────────────────────────────────


class TestCaptureUUID:
    def test_captures_short_and_full(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Capture Me")
        tutor = Tutor()
        tutor.vault = vault
        tutor._capture_uuid("Capture Me", "mykey")
        assert tutor._fmt["mykey"] == meta.uuid[:8]
        assert tutor._fmt["_full_mykey"] == meta.uuid


# ── Resolve UUID ───────────────────────────────────────────────────────


class TestResolveUUID:
    def test_resolves_by_key(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Resolve Me")
        tutor = Tutor()
        tutor.vault = vault
        tutor._fmt = {"_full_mykey": meta.uuid}
        result = tutor._resolve_uuid("mykey")
        assert result == meta.uuid

    def test_falls_back_to_raw(self):
        tutor = Tutor()
        tutor._fmt = {}
        result = tutor._resolve_uuid("raw-uuid-string")
        assert result == "raw-uuid-string"


# ── SHA256 ─────────────────────────────────────────────────────────────


class TestSha256:
    def test_computes_hash(self, vault_dir):
        file_path = os.path.join(vault_dir, "hash_me.txt")
        with open(file_path, "w") as f:
            f.write("test content for sha256")
        tutor = Tutor()
        result = tutor._sha256(file_path)
        assert len(result) == 64
        assert result == sha256_file(file_path)
