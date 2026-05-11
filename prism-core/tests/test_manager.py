import os
import shutil
import tempfile
import uuid

import pytest

from prism.node.manager import NodeManager, resolve_uuid
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.types.builtins import CONTACT_TOML, NOTE_TOML
from prism.vault.vault import Vault


class TestResolveUuid:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        types_dir = os.path.join(d, ".metadata", "types")
        with open(os.path.join(types_dir, "note.toml"), "w") as f:
            f.write(NOTE_TOML)
        yield d
        shutil.rmtree(d)

    def test_full_uuid(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Test")
        resolved = resolve_uuid(vault_dir, meta.uuid)
        assert resolved == meta.uuid

    def test_partial_uuid(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Test")
        resolved = resolve_uuid(vault_dir, meta.uuid[:12])
        assert resolved == meta.uuid

    def test_no_match(self, vault_dir):
        with pytest.raises(ValueError, match="No node found"):
            resolve_uuid(vault_dir, "00000000-0000")

    def test_ambiguous(self, vault_dir):
        uid1 = "aaaaaaaa-0000-0000-0000-000000000001"
        uid2 = "aaaaaaaa-0000-0000-0000-000000000002"
        for uid in [uid1, uid2]:
            storage_dir = compute_storage_path(vault_dir, uid)
            os.makedirs(storage_dir, exist_ok=True)
            meta = NodeMetadata(uuid=uid, type="note", title=f"Node {uid}")
            meta.save(NodeMetadata.metadata_path(storage_dir))
        with pytest.raises(ValueError, match="Multiple nodes match"):
            resolve_uuid(vault_dir, "aaaaaaaa")


class TestNodeManager:
    @pytest.fixture
    def vault_dir(self):
        d = tempfile.mkdtemp()
        Vault.init(d)
        types_dir = os.path.join(d, ".metadata", "types")
        with open(os.path.join(types_dir, "note.toml"), "w") as f:
            f.write(NOTE_TOML)
        with open(os.path.join(types_dir, "contact.toml"), "w") as f:
            f.write(CONTACT_TOML)
        yield d
        shutil.rmtree(d)

    def test_create_note_node(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Test Note", tags=["test"])
        assert meta.type == "note"
        assert meta.title == "Test Note"
        assert meta.tags == ["test"]
        assert meta.blob_extension == "md"
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        assert os.path.exists(NodeMetadata.metadata_path(storage_dir))
        assert os.path.exists(os.path.join(storage_dir, "data.md"))

    def test_create_unknown_type(self, vault_dir):
        manager = NodeManager(vault_dir)
        with pytest.raises(ValueError, match="Unknown type"):
            manager.create_node(type_name="nonexistent")

    def test_create_with_fields(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="John",
            fields={"name": "John Doe", "email": "john@example.com"},
        )
        assert meta.fields["name"] == "John Doe"
        assert meta.fields["email"] == "john@example.com"

    def test_create_with_blob(self, vault_dir):
        manager = NodeManager(vault_dir)
        blob_path = os.path.join(vault_dir, "test.txt")
        with open(blob_path, "w") as f:
            f.write("file content")
        meta = manager.create_node(type_name="note", title="Blob Node", blob_path=blob_path)
        assert meta.blob_extension == "txt"
        assert meta.blob_size > 0
        assert meta.blob_sha256

    def test_create_missing_required_field(self, vault_dir):
        manager = NodeManager(vault_dir)
        with pytest.raises(ValueError, match="required"):
            manager.create_node(type_name="contact", fields={})

    def test_create_no_title(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note")
        assert meta.title == ""
        assert meta.blob_extension == "md"

    def test_show_node(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Show Me", tags=["test"])
        output = manager.show_node(meta.uuid)
        assert output is not None
        assert "Show Me" in output
        assert meta.uuid in output

    def test_show_node_with_links(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Linked Node")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta.links = [{"target": "some-uuid", "title": "link-title"}]
        meta.save(NodeMetadata.metadata_path(storage_dir))
        output = manager.show_node(meta.uuid)
        assert output is not None
        assert "link-title" in output

    def test_show_nonexistent_node(self, vault_dir):
        manager = NodeManager(vault_dir)
        output = manager.show_node("00000000-0000-0000-0000-000000000000")
        assert output is None

    def test_list_nodes(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="Node 1")
        manager.create_node(type_name="note", title="Node 2")
        nodes = manager.list_nodes()
        assert len(nodes) == 2

    def test_rebuild_index(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Index Test")
        with open(manager.index_path, "w") as f:
            f.write("")
        manager.rebuild_index()
        with open(manager.index_path) as f:
            content = f.read()
        assert meta.uuid in content

    def test_delete_node_force(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="To Delete")
        result = manager.delete_node(meta.uuid, force=True)
        assert result is True
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        assert not os.path.exists(storage_dir)

    def test_delete_nonexistent_node(self, vault_dir):
        manager = NodeManager(vault_dir)
        result = manager.delete_node("00000000-0000-0000-0000-000000000000", force=True)
        assert result is False

    def test_find_backlinks(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta_a = manager.create_node(type_name="note", title="Note A")
        meta_b = manager.create_node(type_name="note", title="Note B")
        storage_b = compute_storage_path(vault_dir, meta_b.uuid)
        meta_b.links = [{"target": meta_a.uuid}]
        meta_b.save(NodeMetadata.metadata_path(storage_b))
        backlinks = manager._find_backlinks(meta_a.uuid)
        assert len(backlinks) == 1
        assert backlinks[0]["uuid"] == meta_b.uuid

    def test_find_backlinks_no_storage(self):
        manager = NodeManager("/nonexistent")
        result = manager._find_backlinks("00000000-0000-0000-0000-000000000000")
        assert result == []

    def test_index_add_and_remove(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager._index_add("test-uuid-1")
        manager._index_add("test-uuid-2")
        with open(manager.index_path) as f:
            uids = [line.strip() for line in f if line.strip()]
        assert "test-uuid-1" in uids
        manager._index_remove("test-uuid-1")
        with open(manager.index_path) as f:
            uids = [line.strip() for line in f if line.strip()]
        assert "test-uuid-1" not in uids

    def test_rebuild_index_empty_vault(self):
        temp_dir = tempfile.mkdtemp()
        try:
            Vault.init(temp_dir)
            manager = NodeManager(temp_dir)
            manager.rebuild_index()
            with open(manager.index_path) as f:
                content = f.read()
            assert content == ""
        finally:
            shutil.rmtree(temp_dir)

    def test_show_node_with_fields(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="contact", fields={"name": "Jane", "email": "j@c"})
        output = manager.show_node(meta.uuid)
        assert output is not None
        assert "name" in output
        assert "Jane" in output

    def test_list_nodes_no_storage(self):
        temp_dir = tempfile.mkdtemp()
        try:
            manager = NodeManager(temp_dir)
            nodes = manager.list_nodes()
            assert nodes == []
        finally:
            shutil.rmtree(temp_dir)

    def test_list_nodes_with_corrupt_metadata(self, vault_dir):
        bad_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not valid toml {{{{\n")
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="Good Node")
        nodes = manager.list_nodes()
        assert len(nodes) == 1

    def test_index_remove_no_index(self, vault_dir):
        manager = NodeManager(vault_dir)
        os.unlink(manager.index_path)
        manager._index_remove("test-uuid")

    def test_find_backlinks_with_corrupt_metadata(self, vault_dir):
        bad_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not valid toml {{{{\n")
        manager = NodeManager(vault_dir)
        result = manager._find_backlinks("00000000-0000-0000-0000-000000000000")
        assert result == []
