import os
import shutil
import tempfile

import pytest

from prism.node.manager import NodeManager
from prism.vault.vault import Vault

from prism_cli.completions import (
    resolve_completions,
    complete_command,
    complete_uuid,
    complete_type_name,
    complete_path,
)

ALIASES = {
    "n": "new",
    "s": "show",
    "q": "query",
    "l": "link",
    "bl": "backlinks",
    "g": "graph",
    "st": "status",
    "e": "edit",
    "af": "add-file",
    "v": "verify",
}


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


class TestRootCommandCompletion:
    def test_complete_all_commands(self):
        result = resolve_completions([], "", None, ALIASES)
        assert "init" in result
        assert "open" in result
        assert "help" in result
        assert "exit" in result

    def test_complete_partial(self):
        result = resolve_completions(["n"], "n", None, ALIASES)
        assert "new" in result

    def test_complete_command_no_text(self):
        result = complete_command("", ALIASES)
        assert "init" in result

    def test_complete_command_partial(self):
        result = complete_command("sh", ALIASES)
        assert "show" in result
        assert all(c.startswith("sh") for c in result)


class TestPathSubcommandCompletion:
    def test_path_root(self, vault):
        result = resolve_completions(["path"], "", vault, ALIASES)
        assert "create" in result
        assert "rm" in result
        assert "tree" in result

    def test_path_partial(self, vault):
        result = resolve_completions(["path", "c"], "c", vault, ALIASES)
        assert "create" in result


class TestTagSubcommandCompletion:
    def test_tag_root(self, vault):
        result = resolve_completions(["tag"], "", vault, ALIASES)
        assert "add" in result
        assert "rm" in result
        assert "list" in result
        assert "rename" in result

    def test_tag_add_completes_uuid(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Tag Target")
        parts = ["tag", "add", meta.uuid[:8]]
        result = resolve_completions(parts, meta.uuid[:8], vault, ALIASES)
        assert any(meta.uuid.startswith(r) for r in result)


class TestFlagTriggeredCompletion:
    def test_tag_flag(self, vault):
        result = resolve_completions(["new", "note", "--tag"], "", vault, ALIASES)
        assert isinstance(result, list)

    def test_add_path_flag(self, vault):
        result = resolve_completions(["new", "note", "--add-path"], "", vault, ALIASES)
        assert isinstance(result, list)

    def test_short_add_path_flag(self, vault):
        result = resolve_completions(["edit", "uuid", "-a"], "", vault, ALIASES)
        assert isinstance(result, list)

    def test_remove_path_flag(self, vault):
        result = resolve_completions(["edit", "uuid", "-r"], "", vault, ALIASES)
        assert isinstance(result, list)


class TestTypeNameCompletion:
    def test_complete_type_after_new(self, vault):
        result = resolve_completions(["new"], "", vault, ALIASES)

    def test_complete_type_name_func(self, vault):
        result = complete_type_name(vault, "")
        assert "note" in result
        assert "contact" in result

    def test_complete_type_name_partial(self, vault):
        result = complete_type_name(vault, "con")
        assert "contact" in result


class TestDefaultUuidCompletion:
    def test_complete_after_show(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="UUID Test")
        result = resolve_completions(["show"], "", vault, ALIASES)
        assert any(meta.uuid.startswith(r) for r in result)

    def test_complete_uuid_partial(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="UUID Partial")
        prefix = meta.uuid[:8]
        result = resolve_completions(["show", prefix], prefix, vault, ALIASES)
        assert any(meta.uuid.startswith(r) for r in result)

    def test_complete_uuid_func(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="UUID Func")
        result = complete_uuid(vault, "")
        assert meta.uuid in result

    def test_complete_uuid_empty_vault(self):
        result = complete_uuid(None, "")
        assert result == []


class TestDegradedMode:
    def test_no_vault_returns_empty_for_uuid(self):
        result = resolve_completions(["show"], "", None, ALIASES)
        assert result == []

    def test_no_vault_returns_empty_for_tag(self):
        result = resolve_completions(["new", "note", "--tag"], "", None, ALIASES)
        assert result == []

    def test_commands_still_work_without_vault(self):
        result = resolve_completions([], "", None, ALIASES)
        assert "init" in result
