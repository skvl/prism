import json
import os
import shutil
import tempfile
import uuid as uuid_mod
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.vault import Vault
from prism_cli import commands
from prism_cli.main import cli


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
def runner():
    return CliRunner()


@pytest.fixture
def reg_path(monkeypatch):
    p = Path(tempfile.mkdtemp()) / "vaults.toml"
    monkeypatch.setattr("prism.vault.registry.REGISTRY_PATH", p)
    return p


# ── CLI Group ──────────────────────────────────────────────────────────

class TestCliGroup:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_vault_option_not_found(self, runner):
        result = runner.invoke(cli, ["--vault", "/nonexistent", "status"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_no_subcommand(self, runner):
        result = runner.invoke(cli, [])
        assert result.exit_code == 2

    def test_verbose_flag(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "--verbose", "status"])
        assert result.exit_code == 0

    def test_no_vault_detected(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 1
            assert "No vault found" in result.output


# ── Init ───────────────────────────────────────────────────────────────

class TestInitCommand:
    def test_init_success(self, runner):
        with tempfile.TemporaryDirectory() as d:
            result = runner.invoke(cli, ["init", d])
            assert result.exit_code == 0
            assert "Vault initialized at" in result.output
            assert "Vault UUID:" in result.output
            for tname in ("note.toml", "contact.toml", "bookmark.toml", "file.toml"):
                assert os.path.exists(os.path.join(d, ".metadata", "types", tname))

    def test_init_already_exists(self, runner, vault_dir):
        result = runner.invoke(cli, ["init", vault_dir])
        assert result.exit_code == 1
        assert "Error:" in result.output


# ── Vault Subcommands ──────────────────────────────────────────────────

class TestVaultCommands:
    def test_add_not_found(self, runner):
        result = runner.invoke(cli, ["vault", "add", "/nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_add_success(self, runner, vault_dir, reg_path):
        result = runner.invoke(cli, ["vault", "add", vault_dir])
        assert result.exit_code == 0
        assert "registered" in result.output

    def test_list_empty(self, runner, reg_path):
        result = runner.invoke(cli, ["vault", "list-vaults"])
        assert result.exit_code == 0
        assert "No vaults registered." in result.output

    def test_list_with_vaults(self, runner, vault_dir, reg_path):
        runner.invoke(cli, ["vault", "add", vault_dir])
        result = runner.invoke(cli, ["vault", "list-vaults"])
        assert result.exit_code == 0
        assert vault_dir in result.output

    def test_list_with_exception(self, runner, vault_dir, reg_path):
        runner.invoke(cli, ["vault", "add", vault_dir])
        with patch("prism.node.manager.NodeManager.list_nodes", side_effect=Exception("boom")):
            result = runner.invoke(cli, ["vault", "list-vaults"])
        assert result.exit_code == 0


# ── Add-File ───────────────────────────────────────────────────────────

class TestAddFileCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["add-file", "/some/file"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_file_not_found(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", "/nonexistent/file.txt"])
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_success(self, runner, vault_dir):
        file_path = os.path.join(vault_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello world")
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path])
        assert result.exit_code == 0
        assert "Imported as node" in result.output

    def test_with_type(self, runner, vault_dir):
        file_path = os.path.join(vault_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("content")
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", "--type", "note", file_path])
        assert result.exit_code == 0
        assert "Imported as node" in result.output

    def test_duplicate_decline(self, runner, vault_dir):
        file_path = os.path.join(vault_dir, "dup.txt")
        with open(file_path, "w") as f:
            f.write("dup")
        runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path])
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path], input="n\n")
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_duplicate_accept(self, runner, vault_dir):
        file_path = os.path.join(vault_dir, "dup2.txt")
        with open(file_path, "w") as f:
            f.write("dup")
        runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path])
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path], input="y\n")
        assert result.exit_code == 0

    def test_duplicate_eof(self, runner, vault_dir):
        file_path = os.path.join(vault_dir, "dup3.txt")
        with open(file_path, "w") as f:
            f.write("dup")
        runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path])
        result = runner.invoke(cli, ["--vault", vault_dir, "add-file", file_path], input="")
        assert result.exit_code == 0


# ── New ────────────────────────────────────────────────────────────────

class TestNewCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["new", "note", "Title"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_new_note(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "note", "My Note"])
        assert result.exit_code == 0
        assert "Created note node:" in result.output

    def test_new_unknown_type(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "nonexistent", "Title"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_new_with_tags(self, runner, vault_dir):
        result = runner.invoke(
            cli, ["--vault", vault_dir, "new", "note", "Tagged", "--tag", "foo", "--tag", "bar"]
        )
        assert result.exit_code == 0
        assert "Created note node:" in result.output

    def test_new_no_title(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "note"])
        assert result.exit_code == 0
        assert "Created note node:" in result.output

    def test_new_validation_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "contact"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_new_with_extra_fields(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "contact", "John", "--name=John Doe", "--email=john@test.com"])
        assert result.exit_code == 0
        assert "Created contact node:" in result.output

    def test_new_with_add_path(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/misc"])
        result = runner.invoke(cli, ["--vault", vault_dir, "new", "note", "Path Note", "--add-path", "/misc"])
        assert result.exit_code == 0
        assert "Created note node:" in result.output
        assert "Added path: /misc" in result.output


# ── Edit ───────────────────────────────────────────────────────────────

class TestEditCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["edit", "some-uuid"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_resolve_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_metadata_walk_not_found(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Gone")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        shutil.rmtree(storage_dir)
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid])
        assert result.exit_code == 1
        assert "Node not found" in result.output

    def test_markdown_body_updated(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Editable")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.md")
        with patch("prism.node.manager.NodeManager.get_body_info", return_value=(body_path, 100.0)):
            with patch("subprocess.call"):
                result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12]])
        assert result.exit_code == 0
        assert "Body updated." in result.output

    def test_markdown_no_changes(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Change")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.md")
        with patch("prism.node.manager.NodeManager.get_body_info", return_value=(body_path, os.stat(body_path).st_mtime)):
            with patch("subprocess.call"):
                result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12]])
        assert result.exit_code == 0
        assert "No changes detected." in result.output

    def test_fields_updated(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="contact", title="Edit Me", fields={"name": "Old"})
        schema = manager.type_loader.load("contact")
        with patch("prism.node.manager.NodeManager.get_body_info", return_value=None):
            with patch("prism.node.manager.NodeManager.get_field_info", return_value=(schema, {"name": "Old"})):
                with patch("prism.node.manager.NodeManager.update_node_fields", return_value=True):
                    result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12]], input="\n")
        assert result.exit_code == 0
        assert "Fields updated." in result.output

    def test_fields_no_changes(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="contact", title="No Change", fields={"name": "Same"})
        schema = manager.type_loader.load("contact")
        with patch("prism.node.manager.NodeManager.get_body_info", return_value=None):
            with patch("prism.node.manager.NodeManager.get_field_info", return_value=(schema, {"name": "Same"})):
                with patch("prism.node.manager.NodeManager.update_node_fields", return_value=False):
                    result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12]], input="\n")
        assert result.exit_code == 0
        assert "No changes detected." in result.output

    def test_with_corrupt_metadata(self, runner, vault_dir):
        bad_uid = str(uuid_mod.uuid4())
        bad_storage = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(bad_storage, exist_ok=True)
        with open(NodeMetadata.metadata_path(bad_storage), "w") as f:
            f.write("not valid toml {{\n")
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Valid")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        body_path = os.path.join(storage_dir, "data.md")
        with patch("prism.node.manager.NodeManager.get_body_info", return_value=(body_path, 100.0)):
            with patch("subprocess.call"):
                result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12]])
        assert result.exit_code == 0
        assert "Body updated." in result.output

    def test_edit_add_path(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/test"])
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Edit")
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--add-path", "/test"])
        assert result.exit_code == 0
        assert "Added path: /test" in result.output

    def test_edit_add_path_already_exists(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/test"])
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Edit Dup")
        runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--add-path", "/test"])
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--add-path", "/test"])
        assert result.exit_code == 0
        assert "already associated" in result.output or "already" in result.output

    def test_edit_remove_path(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/test"])
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Rm")
        runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--add-path", "/test"])
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--remove-path", "/test"])
        assert result.exit_code == 0
        assert "Removed path: /test" in result.output

    def test_edit_remove_path_not_associated(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/test"])
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Path Not Assoc")
        result = runner.invoke(cli, ["--vault", vault_dir, "edit", meta.uuid[:12], "--remove-path", "/test"])
        assert result.exit_code == 0
        assert "not associated" in result.output


# ── Rm ─────────────────────────────────────────────────────────────────

class TestRmCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["rm", "some-uuid"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Delete Me")
        result = runner.invoke(cli, ["--vault", vault_dir, "rm", meta.uuid, "--yes"])
        assert result.exit_code == 0
        assert "Deleted node" in result.output

    def test_not_found(self, runner, vault_dir):
        result = runner.invoke(
            cli, ["--vault", vault_dir, "rm", "00000000-0000-0000-0000-000000000000", "--yes"]
        )
        assert result.exit_code == 1
        assert "Node not found" in result.output


# ── Show ───────────────────────────────────────────────────────────────

class TestShowCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["show", "some-uuid"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Show Me")
        result = runner.invoke(cli, ["--vault", vault_dir, "show", meta.uuid[:12]])
        assert result.exit_code == 0
        assert "Show Me" in result.output

    def test_not_found(self, runner, vault_dir):
        result = runner.invoke(
            cli, ["--vault", vault_dir, "show", "00000000-0000-0000-0000-000000000000"]
        )
        assert result.exit_code == 1
        assert "Node not found" in result.output


# ── Link ───────────────────────────────────────────────────────────────

class TestLinkCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["link", "src", "tgt"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_resolve_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "link", "nonexistent", "other"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_source_not_found(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        target = manager.create_node(type_name="note", title="Target")
        result = runner.invoke(
            cli, ["--vault", vault_dir, "link", "00000000-0000-0000-0000-000000000000", target.uuid]
        )
        assert result.exit_code == 1
        assert "Source node not found" in result.output

    def test_target_not_found(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        fake_uuid = str(uuid_mod.uuid4())
        result = runner.invoke(cli, ["--vault", vault_dir, "link", source.uuid, fake_uuid])
        assert result.exit_code == 0
        assert "Warning: Target node does not exist" in result.output
        assert "Linked" in result.output

    def test_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        result = runner.invoke(cli, ["--vault", vault_dir, "link", source.uuid, target.uuid])
        assert result.exit_code == 0
        assert "Linked" in result.output

    def test_already_exists(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        runner.invoke(cli, ["--vault", vault_dir, "link", source.uuid, target.uuid])
        result = runner.invoke(cli, ["--vault", vault_dir, "link", source.uuid, target.uuid])
        assert result.exit_code == 0
        assert "already exists" in result.output

    def test_with_corrupt_metadata(self, runner, vault_dir):
        bad_uid = str(uuid_mod.uuid4())
        bad_storage = compute_storage_path(vault_dir, bad_uid)
        os.makedirs(bad_storage, exist_ok=True)
        with open(NodeMetadata.metadata_path(bad_storage), "w") as f:
            f.write("not valid toml {{\n")
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        result = runner.invoke(cli, ["--vault", vault_dir, "link", source.uuid, target.uuid])
        assert result.exit_code == 0
        assert "Linked" in result.output


# ── Backlinks ──────────────────────────────────────────────────────────

class TestBacklinksCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["backlinks", "some-uuid"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_resolve_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "backlinks", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_no_results(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Lonely")
        result = runner.invoke(cli, ["--vault", vault_dir, "backlinks", meta.uuid])
        assert result.exit_code == 0
        assert "No backlinks found." in result.output

    def test_with_results(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        target = manager.create_node(type_name="note", title="Target")
        source = manager.create_node(type_name="note", title="Source")
        storage_dir = compute_storage_path(vault_dir, source.uuid)
        source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        source_meta.links = [{"target": target.uuid}]
        source_meta.save(NodeMetadata.metadata_path(storage_dir))
        result = runner.invoke(cli, ["--vault", vault_dir, "backlinks", target.uuid[:12]])
        assert result.exit_code == 0
        assert "Source" in result.output


# ── Path Commands ──────────────────────────────────────────────────────

class TestPathCommands:
    def test_path_create(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo/bar"])
        assert result.exit_code == 0
        assert "Path created: /foo/bar" in result.output

    def test_path_rm(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo/bar"])
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "rm", "/foo/bar", "--yes"])
        assert result.exit_code == 0
        assert "Removed path: /foo/bar" in result.output

    def test_path_tree(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo/bar"])
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo/baz"])
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "tree"])
        assert result.exit_code == 0
        assert "foo" in result.output

    def test_path_create_invalid(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "create", ""])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_path_rm_nonexistent(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "rm", "/nonexistent", "--yes"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_path_tree_empty(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "tree"])
        assert result.exit_code == 0

    def test_path_tree_nonexistent(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "path", "tree", "/nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output


# ── Graph ──────────────────────────────────────────────────────────────

class TestGraphCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["graph"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_dot_format(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="Graph Node")
        result = runner.invoke(cli, ["--vault", vault_dir, "graph"])
        assert result.exit_code == 0
        assert "digraph" in result.output

    def test_json_format(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="JSON Node")
        result = runner.invoke(cli, ["--vault", vault_dir, "graph", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "nodes" in data
        assert "edges" in data

    def test_empty_graph_dot(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "graph"])
        assert result.exit_code == 0
        assert "digraph" in result.output

    def test_graph_with_include_paths(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo"])
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="Graph Path")
        result = runner.invoke(cli, ["--vault", vault_dir, "graph", "--include-paths"])
        assert result.exit_code == 0
        assert "digraph" in result.output

    def test_graph_json_include_paths(self, runner, vault_dir):
        runner.invoke(cli, ["--vault", vault_dir, "path", "create", "/foo"])
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="Graph JSON Path")
        result = runner.invoke(cli, ["--vault", vault_dir, "graph", "--format", "json", "--include-paths"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "nodes" in data
        assert "edges" in data


# ── Query ──────────────────────────────────────────────────────────────

class TestQueryCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["query", "tag:test"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_no_results(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "query", "tag:nonexistent"])
        assert result.exit_code == 0
        assert "No results found" in result.output

    def test_table_format(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Query Me", tags=["test"])
        result = runner.invoke(cli, ["--vault", vault_dir, "query", "tag:test"])
        assert result.exit_code == 0
        assert meta.uuid[:12] in result.output
        assert "Query Me" in result.output

    def test_json_format(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="JSON Query", tags=["test"])
        result = runner.invoke(cli, ["--vault", vault_dir, "query", "tag:test", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["uuid"] == meta.uuid

    def test_results_without_tags(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="No Tags")
        result = runner.invoke(cli, ["--vault", vault_dir, "query", "type:note"])
        assert result.exit_code == 0
        assert "No Tags" in result.output

    def test_json_no_tags(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="No Tags JSON")
        result = runner.invoke(cli, ["--vault", vault_dir, "query", "type:note", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) >= 1


# ── Status ─────────────────────────────────────────────────────────────

class TestStatusCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_clean(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "status"])
        assert result.exit_code == 0
        assert "Vault is clean." in result.output

    def test_with_changed(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Changed")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_mtime = "0"
        meta.save(meta_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "status"], input="n\n")
        assert result.exit_code == 0
        assert "Changed nodes:" in result.output

    def test_with_changed_re_extract(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Re-Extract")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_mtime = "0"
        meta.save(meta_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "status"], input="y\n")
        assert result.exit_code == 0

    def test_with_changed_eof(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="EOF Test")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_mtime = "0"
        meta.save(meta_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "status"], input="")
        assert result.exit_code == 0
        assert "Changed nodes:" in result.output

    def test_with_new_files(self, runner, vault_dir):
        with open(os.path.join(vault_dir, "new_file.txt"), "w") as f:
            f.write("new")
        result = runner.invoke(cli, ["--vault", vault_dir, "status"])
        assert result.exit_code == 0
        assert "New files detected" in result.output

    def test_with_orphaned(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Orphaned")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        shutil.rmtree(storage_dir)
        result = runner.invoke(cli, ["--vault", vault_dir, "status"])
        assert result.exit_code == 0
        assert "Missing nodes" in result.output


# ── Verify ─────────────────────────────────────────────────────────────

class TestVerifyCommand:
    def test_no_vault(self, runner, monkeypatch):
        with tempfile.TemporaryDirectory() as tmp:
            monkeypatch.chdir(tmp)
            result = runner.invoke(cli, ["verify", "some-uuid"])
            assert result.exit_code == 1
            assert "No vault found" in result.output

    def test_resolve_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "verify", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_node_not_found(self, runner, vault_dir):
        result = runner.invoke(
            cli, ["--vault", vault_dir, "verify", "00000000-0000-0000-0000-000000000000"]
        )
        assert result.exit_code == 1
        assert "Node not found" in result.output

    def test_ok_with_blob(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        file_path = os.path.join(vault_dir, "verify_ok.txt")
        with open(file_path, "w") as f:
            f.write("verify content")
        meta = manager.create_node(type_name="note", title="Verify Me", blob_path=file_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "verify", meta.uuid[:12]])
        assert result.exit_code == 0
        assert "OK" in result.output

    def test_corrupted(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Corrupted")
        meta_path = NodeMetadata.metadata_path(compute_storage_path(vault_dir, meta.uuid))
        meta = NodeMetadata.from_toml(meta_path)
        meta.blob_sha256 = "0000000000000000000000000000000000000000000000000000000000000000"
        meta.save(meta_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "verify", meta.uuid[:12]])
        assert result.exit_code == 1
        assert "CORRUPTED" in result.output


# ── Tag Commands ───────────────────────────────────────────────────────

class TestTagCommands:
    def test_tag_add_no_vault(self, runner):
        result = runner.invoke(cli, ["--vault", "/nonexistent", "tag", "add", "uuid", "tag"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_add_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Tag Me")
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "add", meta.uuid, "work"])
        assert result.exit_code == 0
        assert "Added tag:" in result.output

    def test_tag_add_already_present(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Tagged", tags=["work"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "add", meta.uuid, "work"])
        assert result.exit_code == 0
        assert "Tag already present" in result.output

    def test_tag_add_invalid(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Bad Tag")
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "add", meta.uuid, "bad tag!"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_add_resolve_error(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "add", "nonexistent", "work"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_add_multiple(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Multi Tag")
        result = runner.invoke(
            cli, ["--vault", vault_dir, "tag", "add", meta.uuid, "work", "personal", "ideas"]
        )
        assert result.exit_code == 0
        assert "Added tag: work" in result.output
        assert "Added tag: personal" in result.output
        assert "Added tag: ideas" in result.output

    def test_tag_rm_no_vault(self, runner):
        result = runner.invoke(cli, ["--vault", "/nonexistent", "tag", "rm", "uuid", "tag"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_rm_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="Remove Tag", tags=["work"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "rm", meta.uuid, "work"])
        assert result.exit_code == 0
        assert "Removed tag:" in result.output

    def test_tag_rm_not_present(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Tag")
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "rm", meta.uuid, "nonexistent"])
        assert result.exit_code == 0
        assert "Tag not present" in result.output

    def test_tag_list_no_vault(self, runner):
        result = runner.invoke(cli, ["--vault", "/nonexistent", "tag", "list"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_list_empty(self, runner, vault_dir):
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "list"])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_tag_list_with_tags(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        manager.create_node(type_name="note", title="B", tags=["work", "personal"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "list"])
        assert result.exit_code == 0
        assert "personal" in result.output
        assert "work" in result.output

    def test_tag_list_with_count(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work", "personal"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "list", "--count"])
        assert result.exit_code == 0
        assert "personal (1)" in result.output
        assert "work (1)" in result.output

    def test_tag_rename_no_vault(self, runner):
        result = runner.invoke(cli, ["--vault", "/nonexistent", "tag", "rename", "old", "new"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_tag_rename_success(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        manager.create_node(type_name="note", title="B", tags=["work", "personal"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "rename", "work", "tasks"])
        assert result.exit_code == 0
        assert "Renamed tag" in result.output
        assert "2 node(s)" in result.output

    def test_tag_rename_invalid(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        manager.create_node(type_name="note", title="A", tags=["work"])
        result = runner.invoke(cli, ["--vault", vault_dir, "tag", "rename", "work", "bad tag!"])
        assert result.exit_code == 1
        assert "Error:" in result.output


# ── Link - Metadata Not Found ──────────────────────────────────────────

class TestLinkMetadataNotFound:
    def test_metadata_not_found(self, runner, vault_dir):
        from prism.node.metadata import NodeMetadata as NM
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        full_uuid = source.uuid
        storage_dir = compute_storage_path(vault_dir, source.uuid)
        shutil.rmtree(storage_dir)

        with patch("prism.node.manager.NodeManager.list_nodes") as mock_list:
            mock_list.return_value = [
                NM(
                    uuid=full_uuid, type="note", title="Source",
                    tags=[], fields={}, links=[],
                    created_at="", updated_at="",
                    blob_extension="", blob_mtime="", blob_size=0, blob_sha256="",
                    sync_dirty=False,
                ),
            ]
            result = runner.invoke(
                cli, ["--vault", vault_dir, "link", full_uuid, target.uuid],
            )

        assert result.exit_code == 1
        assert "Could not find metadata" in result.output

    def test_link_target_not_found_still_links(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        source = manager.create_node(type_name="note", title="Source")
        fake_uuid = str(uuid_mod.uuid4())
        result = runner.invoke(
            cli, ["--vault", vault_dir, "link", source.uuid, fake_uuid],
        )
        assert result.exit_code == 0
        assert "Warning: Target node does not exist" in result.output
        assert "Linked" in result.output


# ── Verify - Blob-less ─────────────────────────────────────────────────

class TestVerifyNoBlob:
    def test_node_without_blob(self, runner, vault_dir):
        manager = NodeManager(vault_dir)
        meta = manager.create_node(type_name="note", title="No Blob")
        storage_dir = compute_storage_path(vault_dir, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_obj = NodeMetadata.from_toml(meta_path)
        meta_obj.blob_sha256 = ""
        meta_obj.save(meta_path)
        result = runner.invoke(cli, ["--vault", vault_dir, "verify", meta.uuid[:12]])
        assert result.exit_code == 1
        assert "CORRUPTED" in result.output


# ── Helper Functions ───────────────────────────────────────────────────

class TestHelperFunctions:
    def test_find_by_hash_found(self, vault_dir):
        manager = NodeManager(vault_dir)
        file_path = os.path.join(vault_dir, "test_find.txt")
        with open(file_path, "w") as f:
            f.write("test content for hash")
        meta = manager.create_node(type_name="note", title="Hash Test", blob_path=file_path)
        result = commands.find_by_hash(manager, meta.blob_sha256)
        assert result.ok
        assert result.data["uuid"] == meta.uuid
        assert result.data["title"] == meta.title

    def test_find_by_hash_not_found(self, vault_dir):
        manager = NodeManager(vault_dir)
        result = commands.find_by_hash(manager, "nonexistent-hash-1234567890")
        assert not result.ok

    def test_write_builtin_types_creates_files(self, vault_dir):
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        for f in os.listdir(types_dir):
            os.unlink(os.path.join(types_dir, f))
        vault = Vault.open(vault_dir)
        commands.write_builtin_types(vault)
        for tname in ("note.toml", "contact.toml", "bookmark.toml", "file.toml"):
            assert os.path.exists(os.path.join(types_dir, tname))

    def test_write_builtin_types_skips_existing(self, vault_dir):
        vault = Vault.open(vault_dir)
        commands.write_builtin_types(vault)
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        for tname in ("note.toml", "contact.toml", "bookmark.toml", "file.toml"):
            assert os.path.exists(os.path.join(types_dir, tname))


# ── __main__ block ─────────────────────────────────────────────────────

class TestMainBlock:
    def test_main_block(self):
        from prism_cli.main import cli as cli_main
        assert cli_main is cli

    def test_main_function(self):
        from prism_cli.main import main
        with pytest.raises(SystemExit):
            main()
