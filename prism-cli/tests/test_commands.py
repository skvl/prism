import os
import shutil
import tempfile
from pathlib import Path

import pytest
from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.vault import Vault
from prism_cli import commands


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
def reg_path(monkeypatch):
    p = tempfile.NamedTemporaryFile(suffix=".toml", delete=False).name
    monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", Path(p))
    return p


class TestCmdResult:
    def test_ok_defaults(self):
        result = commands.CmdResult(ok=True)
        assert result.ok is True
        assert result.error == ""
        assert result.code == ""
        assert result.data == {}

    def test_not_ok_with_error(self):
        result = commands.CmdResult(ok=False, error="something went wrong", code="ERROR")
        assert result.ok is False
        assert result.error == "something went wrong"
        assert result.code == "ERROR"

    def test_with_data(self):
        result = commands.CmdResult(ok=True, data={"uuid": "abc", "name": "test"})
        assert result.data["uuid"] == "abc"


class TestInitOpen:
    def test_init_success(self):
        d = tempfile.mkdtemp()
        result = commands.init_vault(d)
        assert result.ok
        assert result.data["path"] == d
        shutil.rmtree(d)

    def test_init_already_exists(self, vault_dir):
        result = commands.init_vault(vault_dir)
        assert not result.ok
        assert result.code == "ALREADY_EXISTS"

    def test_open_success(self, vault_dir):
        result = commands.open_vault(vault_dir)
        assert result.ok
        assert result.data["path"] == vault_dir

    def test_open_not_found(self):
        result = commands.open_vault("/nonexistent-path-for-test")
        assert not result.ok
        assert result.code == "NOT_FOUND"


class TestCreateNode:
    def test_create_note(self, vault):
        result = commands.create_node(vault, "note", "Test Note")
        assert result.ok
        assert result.data["meta"].title == "Test Note"

    def test_create_with_tags(self, vault):
        result = commands.create_node(vault, "note", "Tagged", tags=["work", "personal"])
        assert result.ok
        meta = result.data["meta"]
        assert "work" in meta.tags
        assert "personal" in meta.tags

    def test_create_with_fields(self, vault):
        result = commands.create_node(
            vault,
            "contact",
            "John",
            fields={"name": "John", "email": "j@test.com"},
        )
        assert result.ok
        assert result.data["meta"].fields.get("name") == "John"

    def test_create_with_add_path(self, vault):
        from prism.path.resolver import PathResolver

        resolver = PathResolver(vault.path)
        resolver.resolve_or_create("/test")
        result = commands.create_node(vault, "note", "Path Note", add_path="/test")
        assert result.ok
        assert result.data["path_added"] == "/test"

    def test_create_unknown_type(self, vault):
        result = commands.create_node(vault, "nonexistent", "Title")
        assert not result.ok
        assert result.code == "VALIDATION_ERROR"

    def test_create_validation_error(self, vault):
        result = commands.create_node(vault, "contact")
        assert not result.ok
        assert result.code == "VALIDATION_ERROR"


class TestShowDeleteVerify:
    def test_show_node_with_description(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(
            type_name="note", title="Show Desc", description="My description"
        )
        result = commands.show_node(vault, meta.uuid, show_description=True)
        assert result.ok
        assert "My description" in result.data["output"]

    def test_show_node_without_description_when_flag_not_set(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(
            type_name="note", title="Hidden Desc", description="Should not appear"
        )
        result = commands.show_node(vault, meta.uuid, show_description=False)
        assert result.ok
        assert "Should not appear" not in result.data["output"]

    def test_show_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Show Me")
        result = commands.show_node(vault, meta.uuid)
        assert result.ok
        assert "Show Me" in result.data["output"]

    def test_show_not_found(self, vault):
        result = commands.show_node(vault, "00000000-0000-0000-0000-000000000000")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_delete_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Delete Me")
        result = commands.delete_node(vault, meta.uuid, force=True)
        assert result.ok
        assert result.data["uuid"] == meta.uuid

    def test_delete_not_found(self, vault):
        result = commands.delete_node(vault, "00000000-0000-0000-0000-000000000000")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_verify_node_with_description(self, vault, vault_dir):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Verify Desc", description="Verify me")
        result = commands.verify_node(vault, meta.uuid[:12])
        assert result.ok
        assert result.data.get("description") == "OK"

    def test_verify_node_without_description(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="No Desc")
        result = commands.verify_node(vault, meta.uuid[:12])
        assert result.ok
        assert result.data.get("description") == ""

    def test_verify_ok(self, vault, vault_dir):
        manager = NodeManager(vault.path)
        file_path = os.path.join(vault_dir, "verify.txt")
        with open(file_path, "w") as f:
            f.write("content")
        meta = manager.create_node(type_name="note", title="Verify", blob_path=file_path)
        result = commands.verify_node(vault, meta.uuid[:12])
        assert result.ok

    def test_verify_not_found(self, vault):
        result = commands.verify_node(vault, "00000000-0000-0000-0000-000000000000")
        assert not result.ok
        assert result.code == "NOT_FOUND"


class TestLinkBacklinks:
    def test_link_success(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        result = commands.link_nodes(vault, source.uuid, target.uuid)
        assert result.ok
        assert result.data["source"] == source.uuid
        assert result.data["target"] == target.uuid

    def test_link_source_not_found(self, vault):
        manager = NodeManager(vault.path)
        target = manager.create_node(type_name="note", title="Target")
        result = commands.link_nodes(vault, "00000000-0000-0000-0000-000000000000", target.uuid)
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_link_already_exists(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        commands.link_nodes(vault, source.uuid, target.uuid)
        result = commands.link_nodes(vault, source.uuid, target.uuid)
        assert not result.ok
        assert result.code == "ALREADY_EXISTS"

    def test_link_target_not_found_warning(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        fake_uuid = "00000000-0000-0000-0000-000000000001"
        result = commands.link_nodes(vault, source.uuid, fake_uuid)
        assert result.ok
        assert "warning" in result.data

    def test_backlinks_with_results(self, vault):
        manager = NodeManager(vault.path)
        target = manager.create_node(type_name="note", title="Target")
        source = manager.create_node(type_name="note", title="Source")
        storage_dir = compute_storage_path(vault.path, source.uuid)
        source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        source_meta.links = [{"target": target.uuid}]
        source_meta.save(NodeMetadata.metadata_path(storage_dir))
        result = commands.list_backlinks(vault, target.uuid[:12])
        assert result.ok
        assert len(result.data["backlinks"]) > 0

    def test_backlinks_no_results(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Lonely")
        result = commands.list_backlinks(vault, meta.uuid)
        assert result.ok
        assert len(result.data["backlinks"]) == 0


class TestListNodes:
    def test_list_nodes_with_desc(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="List Desc", description="Preview text")
        result = commands.list_nodes(vault, show_desc=True)
        assert result.ok
        nodes = result.data["nodes"]
        described = [n for n in nodes if n.get("description")]
        assert len(described) >= 1
        assert "Preview text" in described[0]["description"]

    def test_list_nodes_without_desc(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="No Desc")
        result = commands.list_nodes(vault, show_desc=False)
        assert result.ok
        for n in result.data["nodes"]:
            assert "description" not in n


class TestGraphQueryStatus:
    def test_export_graph_dot(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Graph Node")
        result = commands.export_graph(vault, "dot")
        assert result.ok
        assert "digraph" in result.data["output"]

    def test_export_graph_json(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="JSON Node")
        result = commands.export_graph(vault, "json")
        assert result.ok
        assert "nodes" in result.data["output"]

    def test_query_finds_results(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Query Me", tags=["test"])
        result = commands.query_nodes(vault, "tag:test")
        assert result.ok
        assert len(result.data["results"]) > 0

    def test_query_no_results(self, vault):
        result = commands.query_nodes(vault, "tag:nonexistent")
        assert result.ok
        assert len(result.data["results"]) == 0

    def test_query_text_search(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Search Target", tags=["findme"])
        result = commands.query_nodes(vault, "target")
        assert result.ok
        assert len(result.data["results"]) > 0

    def test_vault_status_clean(self, vault):
        result = commands.vault_status(vault)
        assert result.ok
        report = result.data
        assert "changed" in report
        assert "new_files" in report
        assert "orphaned" in report


class TestImportFile:
    def test_import_success(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "import.txt")
        with open(file_path, "w") as f:
            f.write("hello")
        result = commands.import_file(vault, file_path)
        assert result.ok
        assert "uuid" in result.data

    def test_import_not_found(self, vault):
        result = commands.import_file(vault, "/nonexistent/file.txt")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_import_duplicate(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "dup.txt")
        with open(file_path, "w") as f:
            f.write("dup")
        commands.import_file(vault, file_path)
        result = commands.import_file(vault, file_path)
        assert not result.ok
        assert result.code == "ALREADY_EXISTS"

    def test_import_duplicate_force(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "dup2.txt")
        with open(file_path, "w") as f:
            f.write("dup")
        commands.import_file(vault, file_path)
        result = commands.import_file(vault, file_path, force=True)
        assert result.ok


class TestManageTags:
    def test_tag_add(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tag Me")
        result = commands.manage_tags(vault, "add", meta.uuid, ["work"])
        assert result.ok
        assert result.data["results"][0]["status"] == "added"

    def test_tag_add_already_present(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tagged", tags=["work"])
        result = commands.manage_tags(vault, "add", meta.uuid, ["work"])
        assert result.ok
        assert result.data["results"][0]["status"] == "already_present"

    def test_tag_rm(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Remove", tags=["work"])
        result = commands.manage_tags(vault, "rm", meta.uuid, ["work"])
        assert result.ok
        assert result.data["results"][0]["status"] == "removed"

    def test_tag_list(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work", "personal"])
        result = commands.manage_tags(vault, "list")
        assert result.ok
        assert "work" in result.data["tags"]
        assert "personal" in result.data["tags"]

    def test_tag_rename(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        result = commands.manage_tags(vault, "rename", tags=["work", "tasks"])
        assert result.ok
        assert result.data["affected"] > 0

    def test_tag_add_no_uuid(self, vault):
        result = commands.manage_tags(vault, "add")
        assert not result.ok
        assert result.code == "USAGE"

    def test_tag_unknown_action(self, vault):
        result = commands.manage_tags(vault, "unknown")
        assert not result.ok
        assert result.code == "UNKNOWN_ACTION"


class TestManagePaths:
    def test_path_create(self, vault):
        result = commands.manage_paths(vault, "create", "/foo/bar")
        assert result.ok
        assert result.data["leaf_uuid"] is not None

    def test_path_rm(self, vault):
        commands.manage_paths(vault, "create", "/foo/bar")
        result = commands.manage_paths(vault, "rm", "/foo/bar")
        assert result.ok

    def test_path_tree(self, vault):
        commands.manage_paths(vault, "create", "/foo/bar")
        result = commands.manage_paths(vault, "tree", "/foo")
        assert result.ok
        assert result.data["tree"] is not None

    def test_path_create_no_path(self, vault):
        result = commands.manage_paths(vault, "create", "")
        assert not result.ok
        assert result.code == "USAGE"

    def test_path_rm_not_found(self, vault):
        result = commands.manage_paths(vault, "rm", "/nonexistent")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_path_unknown_action(self, vault):
        result = commands.manage_paths(vault, "unknown")
        assert not result.ok
        assert result.code == "UNKNOWN_ACTION"


class TestSetNodeDescription:
    def test_set_description(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Set Desc")
        result = commands.set_node_description(vault, meta.uuid, "New description")
        assert result.ok
        assert result.data["action"] == "set"
        desc = manager.get_description(meta.uuid)
        assert desc == "New description"

    def test_clear_description(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Clear Desc", description="To clear")
        result = commands.set_node_description(vault, meta.uuid, "")
        assert result.ok
        assert result.data["action"] == "cleared"
        desc = manager.get_description(meta.uuid)
        assert desc is None


class TestEditNode:
    def test_edit_add_path(self, vault):
        from prism.path.resolver import PathResolver

        resolver = PathResolver(vault.path)
        resolver.resolve_or_create("/test")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Edit Path")
        result = commands.edit_node(vault, meta.uuid, add_path="/test")
        assert result.ok
        assert result.data["action"] == "add_path"

    def test_edit_remove_path(self, vault):
        from prism.path.resolver import PathResolver

        resolver = PathResolver(vault.path)
        resolver.resolve_or_create("/test")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Edit Rm")
        manager.add_path_to_node(meta.uuid, "/test")
        result = commands.edit_node(vault, meta.uuid, remove_path="/test")
        assert result.ok
        assert result.data["action"] == "remove_path"

    def test_edit_no_op(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="No Op")
        result = commands.edit_node(vault, meta.uuid)
        assert not result.ok
        assert result.code == "NO_OP"

    def test_edit_body_info(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Body Edit")
        result = commands.edit_node_body(vault, meta.uuid)
        assert result.ok
        assert result.data["type"] == "body"
        assert "body_path" in result.data

    def test_edit_fields_info(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(
            type_name="contact",
            title="Field Edit",
            fields={"name": "Old Name", "email": "old@test.com"},
        )
        result = commands.edit_node_fields(vault, meta.uuid)
        assert result.ok
        assert result.data["type"] == "fields"
        assert "schema" in result.data

    def test_edit_body_not_found(self, vault):
        result = commands.edit_node_body(vault, "00000000-0000-0000-0000-000000000000")
        assert not result.ok
        assert result.code == "NOT_FOUND"


class TestAddListVaults:
    def test_add_vault(self, vault_dir, reg_path):
        result = commands.add_vault(vault_dir)
        assert result.ok
        assert result.data["path"] == vault_dir

    def test_add_vault_not_found(self):
        result = commands.add_vault("/nonexistent-path")
        assert not result.ok
        assert result.code == "NOT_FOUND"

    def test_list_vaults_empty(self, reg_path):
        result = commands.list_vaults()
        assert result.ok
        assert result.data["vaults"] == []

    def test_list_vaults_with_entries(self, vault_dir, reg_path):
        commands.add_vault(vault_dir)
        result = commands.list_vaults()
        assert result.ok
        assert len(result.data["vaults"]) > 0


class TestHelpers:
    def test_write_builtin_types(self, vault_dir):
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        for f in os.listdir(types_dir):
            os.unlink(os.path.join(types_dir, f))
        vault = Vault.open(vault_dir)
        result = commands.write_builtin_types(vault)
        assert result.ok
        for tname in ("note.toml", "contact.toml", "bookmark.toml", "file.toml"):
            assert os.path.exists(os.path.join(types_dir, tname))

    def test_find_by_hash_found(self, vault_dir):
        manager = NodeManager(vault_dir)
        file_path = os.path.join(vault_dir, "helper_find.txt")
        with open(file_path, "w") as f:
            f.write("content for hash")
        meta = manager.create_node(type_name="note", title="Hash Helper", blob_path=file_path)
        result = commands.find_by_hash(manager, meta.blob_sha256)
        assert result.ok
        assert result.data["uuid"] == meta.uuid

    def test_find_by_hash_not_found(self, vault_dir):
        manager = NodeManager(vault_dir)
        result = commands.find_by_hash(manager, "nonexistent-hash-value")
        assert not result.ok
        assert result.code == "NOT_FOUND"
