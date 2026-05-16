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
        assert len(nodes) == 3

    def test_rebuild_index(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Index Test")
        with open(manager.index_path, "w") as f:
            f.write("")
        manager.rebuild_index()
        with open(manager.index_path) as f:
            content = f.read()
        assert meta.uuid in content

    def test_create_node_with_description(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="note", title="Described", description="A brief summary"
        )
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        desc_path = NodeMetadata.description_path(storage_dir)
        assert os.path.exists(desc_path)
        with open(desc_path) as f:
            assert f.read() == "A brief summary"
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.desc_sha256
        assert meta2.desc_mtime
        assert meta2.desc_size > 0

    def test_set_description_on_node_without_one(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Desc")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        desc_path = NodeMetadata.description_path(storage_dir)
        assert not os.path.exists(desc_path)
        meta_obj = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta_obj.desc_sha256 == ""
        manager.set_description(meta.uuid, "New description")
        assert os.path.exists(desc_path)
        with open(desc_path) as f:
            assert f.read() == "New description"
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.desc_sha256
        assert meta2.desc_mtime
        assert meta2.desc_size > 0

    def test_update_existing_description(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Updatable", description="Original")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        manager.set_description(meta.uuid, "Updated description")
        desc_path = NodeMetadata.description_path(storage_dir)
        with open(desc_path) as f:
            assert f.read() == "Updated description"
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.desc_sha256
        assert meta2.desc_size > 0

    def test_clear_description(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Clearable", description="To be cleared")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        desc_path = NodeMetadata.description_path(storage_dir)
        assert os.path.exists(desc_path)
        manager.set_description(meta.uuid, "")
        assert not os.path.exists(desc_path)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.desc_sha256 == ""
        assert meta2.desc_size == 0

    def test_delete_node_with_description(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="note", title="Delete Desc", description="Will be deleted"
        )
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        assert os.path.exists(NodeMetadata.description_path(storage_dir))
        manager.delete_node(meta.uuid, force=True)
        assert not os.path.exists(storage_dir)

    def test_description_link_extraction(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Link Desc")
        target_uuid = "aaaaaaaa-0000-0000-0000-000000000000"
        manager.set_description(meta.uuid, f"See [[{target_uuid}]] for details")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert len(meta2.links) == 1
        assert meta2.links[0]["target"] == target_uuid

    def test_description_without_links(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Link Desc")
        manager.set_description(meta.uuid, "Plain text without any links")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.links == []

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
            nodes = manager.list_nodes()
            assert any(n.type == "path" for n in nodes)  # root path node created on init
            manager.rebuild_index()
            with open(manager.index_path) as f:
                content = f.read()
            assert len(content.strip()) > 0
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
        assert len(nodes) == 2

    def test_index_remove_no_index(self, vault_dir):
        manager = NodeManager(vault_dir)
        os.unlink(manager.index_path)
        manager._index_remove("test-uuid")

    def test_add_tag(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Tag Me")
        assert manager.add_tag(meta.uuid, "work") is True
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert "work" in meta2.tags

    def test_add_tag_already_present(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Tagged", tags=["work"])
        assert manager.add_tag(meta.uuid, "work") is False

    def test_add_tag_invalid(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Bad Tag")
        with pytest.raises(ValueError, match="Invalid tag"):
            manager.add_tag(meta.uuid, "bad tag!")

    def test_add_tag_node_not_found(self, vault_dir):
        manager = NodeManager(vault_dir)
        with pytest.raises(ValueError, match="Node not found"):
            manager.add_tag("00000000-0000-0000-0000-000000000000", "work")

    def test_remove_tag(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Remove Tags", tags=["work", "personal"])
        assert manager.remove_tag(meta.uuid, "work") is True
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert "work" not in meta2.tags
        assert "personal" in meta2.tags

    def test_remove_tag_not_present(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Tag")
        assert manager.remove_tag(meta.uuid, "nonexistent") is False

    def test_list_tags(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        manager.create_node(type_name="note", title="B", tags=["work", "personal"])
        result = manager.list_tags()
        assert result == {"personal": 1, "work": 2}

    def test_list_tags_empty(self, vault_dir):
        manager = NodeManager(vault_dir)
        assert manager.list_tags() == {}

    def test_rename_tag(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        manager.create_node(type_name="note", title="B", tags=["work", "personal"])
        affected = manager.rename_tag("work", "tasks")
        assert affected == 2
        result = manager.list_tags()
        assert "work" not in result
        assert result.get("tasks") == 2
        assert result.get("personal") == 1

    def test_rename_tag_deduplicates(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work", "tasks"])
        affected = manager.rename_tag("work", "tasks")
        assert affected == 1
        result = manager.list_tags()
        assert result.get("tasks") == 1
        assert "work" not in result

    def test_rename_tag_invalid_new(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        with pytest.raises(ValueError, match="Invalid tag"):
            manager.rename_tag("work", "bad tag!")

    def test_rename_tag_same_name(self, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        affected = manager.rename_tag("work", "work")
        assert affected == 0

    def test_find_backlinks_with_corrupt_metadata(self, vault_dir):
        bad_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(storage_dir, exist_ok=True)
        with open(NodeMetadata.metadata_path(storage_dir), "w") as f:
            f.write("not valid toml {{{{\n")
        manager = NodeManager(vault_dir)
        result = manager._find_backlinks("00000000-0000-0000-0000-000000000000")
        assert result == []

    def test_delete_node_force_with_backlinks(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta_a = manager.create_node(type_name="note", title="Note A")
        meta_b = manager.create_node(type_name="note", title="Note B")
        storage_b = compute_storage_path(vault_dir, meta_b.uuid)
        meta_b.links = [{"target": meta_a.uuid}]
        meta_b.save(NodeMetadata.metadata_path(storage_b))
        result = manager.delete_node(meta_a.uuid, force=True)
        assert result is True
        storage_dir_a = compute_storage_path(vault_dir, meta_a.uuid)
        assert not os.path.exists(storage_dir_a)

    def test_delete_nonexistent_node_no_force(self, vault_dir):
        manager = NodeManager(vault_dir)
        result = manager.delete_node("00000000-0000-0000-0000-000000000000")
        assert result is False

    def test_show_node_with_path(self, vault_dir):
        import tomlkit

        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Node")
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        root_uuid = doc["path_root_uuid"]
        path_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, path_uid)
        os.makedirs(storage_dir, exist_ok=True)
        path_meta = NodeMetadata(
            uuid=path_uid,
            type="path",
            title="mypath",
            fields={"name": "mypath"},
            links=[{"target": root_uuid, "type": "path-parent", "title": ".."}],
        )
        path_meta.save(NodeMetadata.metadata_path(storage_dir))
        storage_dir2 = compute_storage_path(vault_dir, meta.uuid)
        meta.paths = [path_uid]
        meta.save(NodeMetadata.metadata_path(storage_dir2))
        output = manager.show_node(meta.uuid)
        assert output is not None
        assert "/mypath" in output

    def test_get_body_info_existing(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Body Test")
        result = manager.get_body_info(meta.uuid)
        assert result is not None
        path, mtime = result
        assert path.endswith("data.md")
        assert os.path.exists(path)
        assert isinstance(mtime, float)

    def test_get_body_info_no_blob_extension(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="No Body",
            fields={"name": "X", "email": "x@x"},
        )
        result = manager.get_body_info(meta.uuid)
        assert result is None

    def test_get_body_info_nonexistent_body_file(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Missing Body")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        os.unlink(os.path.join(storage_dir, "data.md"))
        result = manager.get_body_info(meta.uuid)
        assert result is None

    def test_commit_body_edit_md_with_link_extraction(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Link Extract")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.md")
        target_uuid = "aaaaaaaa-0000-0000-0000-000000000000"
        with open(body_path, "w") as f:
            f.write(f"[[{target_uuid}]]\n")
        stat_info = os.stat(body_path)
        manager.commit_body_edit(meta.uuid, stat_info.st_mtime, stat_info.st_size, "abc123")
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert len(meta2.links) == 1
        assert meta2.links[0]["target"] == target_uuid

    def test_commit_body_edit_non_md_no_link_extraction(self, vault_dir):
        manager = NodeManager(vault_dir)
        blob_path = os.path.join(vault_dir, "test.txt")
        with open(blob_path, "w") as f:
            f.write("plain text")
        meta = manager.create_node(type_name="note", title="Non MD", blob_path=blob_path)
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.txt")
        with open(body_path, "w") as f:
            f.write("[[some-uuid]]\n")
        stat_info = os.stat(body_path)
        manager.commit_body_edit(meta.uuid, stat_info.st_mtime, stat_info.st_size, "def456")
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.links == []

    def test_commit_body_edit_links_updated(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Link Update")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.md")
        old_uuid = "bbbbbbbb-0000-0000-0000-000000000001"
        with open(body_path, "w") as f:
            f.write(f"[[{old_uuid}]]\n")
        stat_info = os.stat(body_path)
        manager.commit_body_edit(meta.uuid, stat_info.st_mtime, stat_info.st_size, "ghi789")
        new_uuid = "cccccccc-0000-0000-0000-000000000002"
        with open(body_path, "w") as f:
            f.write(f"[[{new_uuid}]]\n")
        stat_info2 = os.stat(body_path)
        manager.commit_body_edit(meta.uuid, stat_info2.st_mtime, stat_info2.st_size, "jkl012")
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert len(meta2.links) == 1
        assert meta2.links[0]["target"] == new_uuid

    def test_get_field_info_existing(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="Field Test",
            fields={"name": "Alice", "email": "a@b"},
        )
        schema, values = manager.get_field_info(meta.uuid)
        assert schema.name == "contact"
        assert values["name"] == "Alice"
        assert values["email"] == "a@b"

    def test_get_field_info_nonexistent_type(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Bad Type")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_from_disk = NodeMetadata.from_toml(meta_path)
        meta_from_disk.type = "nonexistent"
        meta_from_disk.save(meta_path)
        with pytest.raises(ValueError, match="Unknown type"):
            manager.get_field_info(meta.uuid)

    def test_update_node_fields_single(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="Single Update",
            fields={"name": "Old", "email": "o@o"},
        )
        assert manager.update_node_fields(meta.uuid, {"name": "New"}) is True
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.fields["name"] == "New"
        assert meta2.fields["email"] == "o@o"

    def test_update_node_fields_multiple(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="Multi Update",
            fields={"name": "A", "email": "a@a"},
        )
        assert manager.update_node_fields(meta.uuid, {"name": "B", "email": "b@b"}) is True
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        assert meta2.fields["name"] == "B"
        assert meta2.fields["email"] == "b@b"

    def test_update_node_fields_empty_changes(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(
            type_name="contact",
            title="Empty Update",
            fields={"name": "X", "email": "x@x"},
        )
        assert manager.update_node_fields(meta.uuid, {}) is False

    def test_delete_node_raises_value_error_on_backlinks(self, vault_dir):
        manager = NodeManager(vault_dir)
        meta_a = manager.create_node(type_name="note", title="Note A")
        meta_b = manager.create_node(type_name="note", title="Note B")
        storage_b = compute_storage_path(vault_dir, meta_b.uuid)
        meta_b.links = [{"target": meta_a.uuid}]
        meta_b.save(NodeMetadata.metadata_path(storage_b))
        with pytest.raises(ValueError, match=r"node\(s\) link to this node"):
            manager.delete_node(meta_a.uuid)

    def test_add_path_to_node(self, vault_dir):
        import tomlkit

        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Add")
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        root_uuid = doc["path_root_uuid"]
        path_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, path_uid)
        os.makedirs(storage_dir, exist_ok=True)
        path_meta = NodeMetadata(
            uuid=path_uid,
            type="path",
            title="testpath",
            fields={"name": "testpath"},
            links=[{"target": root_uuid, "type": "path-parent", "title": ".."}],
        )
        path_meta.save(NodeMetadata.metadata_path(storage_dir))
        assert manager.add_path_to_node(meta.uuid, "/testpath") is True
        storage_dir2 = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir2))
        assert path_uid in meta2.paths

    def test_add_path_to_node_duplicate(self, vault_dir):
        import tomlkit

        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Dup")
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        root_uuid = doc["path_root_uuid"]
        path_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, path_uid)
        os.makedirs(storage_dir, exist_ok=True)
        path_meta = NodeMetadata(
            uuid=path_uid,
            type="path",
            title="testpath2",
            fields={"name": "testpath2"},
            links=[{"target": root_uuid, "type": "path-parent", "title": ".."}],
        )
        path_meta.save(NodeMetadata.metadata_path(storage_dir))
        manager.add_path_to_node(meta.uuid, "/testpath2")
        assert manager.add_path_to_node(meta.uuid, "/testpath2") is False

    def test_remove_path_from_node(self, vault_dir):
        import tomlkit

        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Remove")
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        root_uuid = doc["path_root_uuid"]
        path_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, path_uid)
        os.makedirs(storage_dir, exist_ok=True)
        path_meta = NodeMetadata(
            uuid=path_uid,
            type="path",
            title="testpath3",
            fields={"name": "testpath3"},
            links=[{"target": root_uuid, "type": "path-parent", "title": ".."}],
        )
        path_meta.save(NodeMetadata.metadata_path(storage_dir))
        manager.add_path_to_node(meta.uuid, "/testpath3")
        assert manager.remove_path_from_node(meta.uuid, "/testpath3") is True
        storage_dir2 = compute_storage_path(vault_dir, meta.uuid)
        meta2 = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir2))
        assert path_uid not in meta2.paths

    def test_remove_path_from_node_not_present(self, vault_dir):
        import tomlkit

        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Not Present")
        with open(os.path.join(vault_dir, ".metadata", "vault.toml")) as f:
            doc = tomlkit.load(f)
        root_uuid = doc["path_root_uuid"]
        path_uid = str(uuid.uuid4())
        storage_dir = compute_storage_path(vault_dir, path_uid)
        os.makedirs(storage_dir, exist_ok=True)
        path_meta = NodeMetadata(
            uuid=path_uid,
            type="path",
            title="orphanpath",
            fields={"name": "orphanpath"},
            links=[{"target": root_uuid, "type": "path-parent", "title": ".."}],
        )
        path_meta.save(NodeMetadata.metadata_path(storage_dir))
        assert manager.remove_path_from_node(meta.uuid, "/orphanpath") is False
