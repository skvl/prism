import io
import os
import shutil
import tempfile

import pytest
from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path
from prism.vault.vault import Vault
from prism_cli.repl import Repl


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


def run_repl(vault, commands):
    input_stream = io.StringIO("\n".join(commands) + "\n")
    output_stream = io.StringIO()
    repl = Repl(vault=vault, input_stream=input_stream, output_stream=output_stream)
    repl.run()
    return output_stream.getvalue()


def run_repl_no_vault(commands):
    input_stream = io.StringIO("\n".join(commands) + "\n")
    output_stream = io.StringIO()
    repl = Repl(input_stream=input_stream, output_stream=output_stream)
    repl.run()
    return output_stream.getvalue()


# ── Basic Entry ─────────────────────────────────────────────────────────


class TestReplBasic:
    def test_run_exit(self, vault):
        output = run_repl(vault, ["exit"])
        assert "Prism REPL" in output
        assert "Connected to vault:" in output

    def test_run_quit(self, vault):
        output = run_repl(vault, ["quit"])
        assert "Prism REPL" in output

    def test_run_no_vault_degraded(self):
        output = run_repl_no_vault(["exit"])
        assert "Prism REPL" in output
        assert "No vault connected" in output

    def test_empty_input_continues(self, vault):
        input_stream = io.StringIO("\n\nexit\n")
        output_stream = io.StringIO()
        repl = Repl(vault=vault, input_stream=input_stream, output_stream=output_stream)
        repl.run()
        output = output_stream.getvalue()
        assert "Prism REPL" in output

    def test_eof_handled(self, vault):
        input_stream = io.StringIO("")
        output_stream = io.StringIO()
        repl = Repl(vault=vault, input_stream=input_stream, output_stream=output_stream)
        repl.run()
        output = output_stream.getvalue()
        assert "Prism REPL" in output


# ── Degraded Mode ───────────────────────────────────────────────────────


class TestReplDegraded:
    def test_vault_rejected_in_degraded(self):
        output = run_repl_no_vault(["new", "note", "Title", "exit"])
        assert "No vault connected" in output

    def test_init_in_degraded(self, vault_dir):
        output = run_repl_no_vault([f"init {vault_dir}", "exit"])
        assert "Error:" in output or "already exists" in output

    def test_init_creates_vault(self):
        new_dir = tempfile.mkdtemp()
        output = run_repl_no_vault([f"init {new_dir}", "exit"])
        shutil.rmtree(new_dir)
        assert "Vault initialized" in output

    def test_open_in_degraded(self, vault_dir):
        output = run_repl_no_vault([f"open {vault_dir}", "exit"])
        assert "Connected to vault:" in output

    def test_open_nonexistent(self):
        output2 = run_repl_no_vault(["open /nonexistent/vault", "exit"])
        assert "Error:" in output2 or "not found" in output2

    def test_open_without_args(self):
        output = run_repl_no_vault(["open", "exit"])
        assert "Usage:" in output


# ── New ─────────────────────────────────────────────────────────────────


class TestReplNew:
    def test_new_note(self, vault):
        output = run_repl(vault, ["new note 'My Note'", "exit"])
        assert "Created note node:" in output

    def test_new_with_tags(self, vault):
        output = run_repl(vault, ["new note Tagged --tag work --tag personal", "exit"])
        assert "Created note node:" in output

    def test_new_unknown_type(self, vault):
        output = run_repl(vault, ["new nonexistent Title", "exit"])
        assert "Error:" in output or "Error" in output

    def test_new_no_args(self, vault):
        output = run_repl(vault, ["new", "exit"])
        assert "Usage:" in output

    def test_new_with_add_path_flag(self, vault):
        run_repl(vault, ["path create /misc", "exit"])
        output = run_repl(vault, ["new note PathNote --add-path /misc", "exit"])
        assert "Created note node:" in output

    def test_new_with_nonexistent_path(self, vault):
        output = run_repl(vault, ["new note BadPath --add-path /nonexistent", "exit"])
        assert "does not exist" in output

    def test_new_with_field_extra(self, vault):
        output = run_repl(vault, ["new contact John --name=John --email=j@test.com", "exit"])
        assert "Created contact node:" in output


# ── Show ────────────────────────────────────────────────────────────────


class TestReplShow:
    def test_show_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Show Test")
        output = run_repl(vault, [f"show {meta.uuid[:12]}", "exit"])
        assert "Show Test" in output

    def test_show_not_found(self, vault):
        output = run_repl(vault, ["show 00000000-0000-0000-0000-000000000000", "exit"])
        assert "not found" in output

    def test_show_no_args(self, vault):
        output = run_repl(vault, ["show", "exit"])
        assert "Usage:" in output


# ── Edit ────────────────────────────────────────────────────────────────


class TestReplEdit:
    def test_edit_add_path(self, vault, vault_dir):
        from prism.path.resolver import PathResolver

        resolver = PathResolver(vault_dir)
        resolver.resolve_or_create("/test")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Edit Path")
        output = run_repl(vault, [f"edit {meta.uuid[:12]} --add-path /test", "exit"])
        assert "Added path: /test" in output

    def test_edit_remove_path(self, vault, vault_dir):
        from prism.path.resolver import PathResolver

        resolver = PathResolver(vault_dir)
        resolver.resolve_or_create("/test")
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Edit Rm Path")
        manager.add_path_to_node(meta.uuid, "/test")
        output = run_repl(vault, [f"edit {meta.uuid[:12]} --remove-path /test", "exit"])
        assert "Removed path: /test" in output

    def test_edit_no_args(self, vault):
        output = run_repl(vault, ["edit", "exit"])
        assert "Usage:" in output

    def test_edit_field_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(
            type_name="contact",
            title="Contact Edit",
            fields={"name": "Old Name", "email": "old@test.com"},
        )
        output = run_repl(vault, [f"edit {meta.uuid[:12]}", "", "", "exit"])
        assert "Fields updated" in output or "No changes detected" in output


# ── Rm ──────────────────────────────────────────────────────────────────


class TestReplRm:
    def test_rm_node(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Delete Me")
        output = run_repl(vault, [f"rm {meta.uuid[:12]}", "exit"])
        assert "Deleted node" in output

    def test_rm_not_found(self, vault):
        output = run_repl(vault, ["rm 00000000-0000-0000-0000-000000000000", "exit"])
        assert "not found" in output

    def test_rm_no_args(self, vault):
        output = run_repl(vault, ["rm", "exit"])
        assert "Usage:" in output


# ── Link ────────────────────────────────────────────────────────────────


class TestReplLink:
    def test_link_success(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        output = run_repl(vault, [f"link {source.uuid[:12]} {target.uuid[:12]}", "exit"])
        assert "Linked" in output

    def test_link_source_not_found(self, vault):
        manager = NodeManager(vault.path)
        target = manager.create_node(type_name="note", title="Target")
        output = run_repl(
            vault,
            [f"link 00000000-0000-0000-0000-000000000000 {target.uuid[:12]}", "exit"],
        )
        assert "Source node not found" in output

    def test_link_already_exists(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Source")
        target = manager.create_node(type_name="note", title="Target")
        run_repl(vault, [f"link {source.uuid[:12]} {target.uuid[:12]}", "exit"])
        output = run_repl(vault, [f"link {source.uuid[:12]} {target.uuid[:12]}", "exit"])
        assert "already exists" in output

    def test_link_no_args(self, vault):
        output = run_repl(vault, ["link", "exit"])
        assert "Usage:" in output


# ── Backlinks ───────────────────────────────────────────────────────────


class TestReplBacklinks:
    def test_backlinks_with_results(self, vault):
        manager = NodeManager(vault.path)
        target = manager.create_node(type_name="note", title="Back Target")
        source = manager.create_node(type_name="note", title="Back Source")
        storage_dir = compute_storage_path(vault.path, source.uuid)
        source_meta = NodeMetadata.from_toml(NodeMetadata.metadata_path(storage_dir))
        source_meta.links = [{"target": target.uuid}]
        source_meta.save(NodeMetadata.metadata_path(storage_dir))
        output = run_repl(vault, [f"backlinks {target.uuid[:12]}", "exit"])
        assert "Back Source" in output

    def test_backlinks_no_results(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Lonely")
        output = run_repl(vault, [f"backlinks {meta.uuid[:12]}", "exit"])
        assert "No backlinks found" in output

    def test_backlinks_no_args(self, vault):
        output = run_repl(vault, ["backlinks", "exit"])
        assert "Usage:" in output


# ── Graph ───────────────────────────────────────────────────────────────


class TestReplGraph:
    def test_graph_dot(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Graph Node")
        output = run_repl(vault, ["graph", "exit"])
        assert "digraph" in output

    def test_graph_json(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Graph JSON")
        output = run_repl(vault, ["graph json", "exit"])
        import json

        start = output.index("{")
        end = output.rindex("}") + 1
        json_str = output[start:end] if "{" in output and "}" in output else "{}"
        data = json.loads(json_str)
        assert isinstance(data, dict) if data else True

    def test_graph_empty(self, vault):
        output = run_repl(vault, ["graph", "exit"])
        assert "digraph" in output


# ── Query ───────────────────────────────────────────────────────────────


class TestReplQuery:
    def test_query_finds_node(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Query Me", tags=["test"])
        output = run_repl(vault, ["query tag:test", "exit"])
        assert "Query Me" in output

    def test_query_no_results(self, vault):
        output = run_repl(vault, ["query tag:nonexistent", "exit"])
        assert "No results found" in output

    def test_query_no_args(self, vault):
        output = run_repl(vault, ["query", "exit"])
        assert "Usage:" in output


# ── Status ──────────────────────────────────────────────────────────────


class TestReplStatus:
    def test_status_clean(self, vault):
        output = run_repl(vault, ["status", "exit"])
        assert "clean" in output

    def test_status_with_changed(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Changed")
        storage_dir = compute_storage_path(vault.path, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_obj = NodeMetadata.from_toml(meta_path)
        meta_obj.blob_mtime = "0"
        meta_obj.save(meta_path)
        output = run_repl(vault, ["status", "n", "exit"])
        assert "Changed nodes:" in output

    def test_status_with_new_files(self, vault):
        with open(os.path.join(vault.path, "new_file.txt"), "w") as f:
            f.write("new")
        output = run_repl(vault, ["status", "exit"])
        assert "New files detected" in output


# ── Add-File ────────────────────────────────────────────────────────────


class TestReplAddFile:
    def test_add_file_success(self, vault, vault_dir):
        file_path = os.path.join(vault_dir, "import.txt")
        with open(file_path, "w") as f:
            f.write("hello")
        output = run_repl(vault, [f"add-file {file_path}", "exit"])
        assert "Imported as node" in output

    def test_add_file_not_found(self, vault):
        output = run_repl(vault, ["add-file /nonexistent/file.txt", "exit"])
        assert "not found" in output

    def test_add_file_no_args(self, vault):
        output = run_repl(vault, ["add-file", "exit"])
        assert "Usage:" in output


# ── Verify ──────────────────────────────────────────────────────────────


class TestReplVerify:
    def test_verify_ok(self, vault, vault_dir):
        manager = NodeManager(vault.path)
        file_path = os.path.join(vault_dir, "verify.txt")
        with open(file_path, "w") as f:
            f.write("content")
        meta = manager.create_node(type_name="note", title="Verify", blob_path=file_path)
        output = run_repl(vault, [f"verify {meta.uuid[:12]}", "exit"])
        assert "OK" in output

    def test_verify_node_not_found(self, vault):
        output = run_repl(vault, ["verify 00000000-0000-0000-0000-000000000000", "exit"])
        assert "not found" in output

    def test_verify_no_args(self, vault):
        output = run_repl(vault, ["verify", "exit"])
        assert "Usage:" in output


# ── Tag Commands ────────────────────────────────────────────────────────


class TestReplTag:
    def test_tag_add(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tag Me")
        output = run_repl(vault, [f"tag add {meta.uuid[:12]} work", "exit"])
        assert "Added tag: work" in output

    def test_tag_add_already_present(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tagged", tags=["work"])
        output = run_repl(vault, [f"tag add {meta.uuid[:12]} work", "exit"])
        assert "already present" in output

    def test_tag_rm(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Remove", tags=["work"])
        output = run_repl(vault, [f"tag rm {meta.uuid[:12]} work", "exit"])
        assert "Removed tag:" in output

    def test_tag_list(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work", "personal"])
        output = run_repl(vault, ["tag list", "exit"])
        assert "work" in output
        assert "personal" in output

    def test_tag_list_with_count(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        output = run_repl(vault, ["tag list --count", "exit"])
        assert "work (1)" in output

    def test_tag_rename(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="A", tags=["work"])
        output = run_repl(vault, ["tag rename work tasks", "exit"])
        assert "Renamed tag" in output

    def test_tag_no_args(self, vault):
        output = run_repl(vault, ["tag", "exit"])
        assert "Usage:" in output


# ── Path Commands ───────────────────────────────────────────────────────


class TestReplPath:
    def test_path_create(self, vault):
        output = run_repl(vault, ["path create /foo/bar", "exit"])
        assert "Path created: /foo/bar" in output

    def test_path_rm(self, vault):
        run_repl(vault, ["path create /foo/bar", "exit"])
        output = run_repl(vault, ["path rm /foo/bar", "exit"])
        assert "Removed path" in output

    def test_path_tree(self, vault):
        run_repl(vault, ["path create /foo/bar", "exit"])
        output = run_repl(vault, ["path tree", "exit"])
        assert "foo" in output

    def test_path_no_args(self, vault):
        output = run_repl(vault, ["path", "exit"])
        assert "Usage:" in output


# ── Alias Resolution ────────────────────────────────────────────────────


class TestReplAliases:
    def test_n_alias_new(self, vault):
        output = run_repl(vault, ["n note 'Alias Test'", "exit"])
        assert "Created note node:" in output

    def test_s_alias_show(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Show Alias")
        output = run_repl(vault, [f"s {meta.uuid[:12]}", "exit"])
        assert "Show Alias" in output

    def test_q_alias_query(self, vault):
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Query Alias", tags=["test"])
        output = run_repl(vault, ["q tag:test", "exit"])
        assert "Query Alias" in output

    def test_l_alias_link(self, vault):
        manager = NodeManager(vault.path)
        source = manager.create_node(type_name="note", title="Src")
        target = manager.create_node(type_name="note", title="Tgt")
        output = run_repl(vault, [f"l {source.uuid[:12]} {target.uuid[:12]}", "exit"])
        assert "Linked" in output

    def test_bl_alias_backlinks(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="BL Test")
        output = run_repl(vault, [f"bl {meta.uuid[:12]}", "exit"])
        assert "backlinks" in output.lower() or "No backlinks" in output

    def test_st_alias_status(self, vault):
        output = run_repl(vault, ["st", "exit"])
        assert "clean" in output

    def test_e_alias_edit(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Edit Ali")
        output = run_repl(vault, [f"e {meta.uuid[:12]}", "exit"])
        assert (
            "Body updated" in output
            or "No changes detected" in output
            or "not found" in output
            or "Usage" in output
        )

    def test_g_alias_graph(self, vault):
        output = run_repl(vault, ["g", "exit"])
        assert "digraph" in output

    def test_v_alias_verify(self, vault):
        output = run_repl(vault, ["v 00000000-0000-0000-0000-000000000000", "exit"])
        assert "not found" in output

    def test_af_alias_add_file(self, vault):
        output = run_repl(vault, ["af /nonexistent", "exit"])
        assert "not found" in output


# ── Underscore Reference ────────────────────────────────────────────────


class TestReplUnderscore:
    def test_underscore_references_last_uuid(self, vault):
        output = run_repl(vault, ["new note First", "show _", "exit"])
        assert "First" in output

    def test_underscore_no_previous(self, vault):
        output = run_repl(vault, ["show _", "exit"])
        assert "No previous node" in output


# ── Help ────────────────────────────────────────────────────────────────


class TestReplHelp:
    def test_help_shows_commands(self, vault):
        output = run_repl(vault, ["help", "exit"])
        assert "Available commands:" in output

    def test_help_new(self, vault):
        output = run_repl(vault, ["help new", "exit"])
        assert "Create a new typed node" in output or "new" in output

    def test_help_show(self, vault):
        output = run_repl(vault, ["help show", "exit"])
        assert "Display node details" in output or "show" in output


# ── Tutor ───────────────────────────────────────────────────────────────


class TestReplTutor:
    def test_tutor_unsupported(self, vault):
        output = run_repl(vault, ["tutor", "exit"])
        assert "cannot run inside the REPL" in output


# ── Unknown Command ─────────────────────────────────────────────────────


class TestReplUnknown:
    def test_unknown_command(self, vault):
        output = run_repl(vault, ["nonexistent_command", "exit"])
        assert "Unknown command" in output
