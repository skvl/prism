import os
import shutil
import tempfile

import pytest

from prism.vault.vault import Vault
from prism_cli import commands
from prism_cli import completions
from prism_cli.repl import ALIASES, Repl


class TestReplDegradedMode:
    @pytest.fixture
    def repl(self):
        return Repl(vault=None)

    def test_degraded_blocks_vault_command(self, repl, capsys):
        repl._handle_line("new note Title")
        captured = capsys.readouterr()
        assert "No vault connected" in captured.out

    def test_init_transitions_to_full_mode(self, repl):
        d = tempfile.mkdtemp()
        try:
            repl._handle_line(f"init {d}")
            assert repl.vault is not None
            assert repl.vault.path == os.path.realpath(d)
        finally:
            shutil.rmtree(d)

    def test_open_transitions_to_full_mode(self, repl):
        d = tempfile.mkdtemp()
        try:
            vault = Vault.init(d)
            commands.write_builtin_types(vault)
            repl._handle_line(f"open {d}")
            assert repl.vault is not None
            assert repl.vault.vault_uuid == vault.vault_uuid
        finally:
            shutil.rmtree(d)

    def test_unsupported_command_shows_warning(self, repl, capsys):
        repl._handle_line("tutor")
        captured = capsys.readouterr()
        assert "cannot run inside the REPL" in captured.out

    def test_exit_returns_true(self, repl):
        assert repl._handle_line("exit") is True

    def test_quit_returns_true(self, repl):
        assert repl._handle_line("quit") is True

    def test_help_available_in_degraded_mode(self, repl, capsys):
        repl._handle_line("help")
        captured = capsys.readouterr()
        assert "Available commands" in captured.out


class TestReplFullMode:
    @pytest.fixture
    def vault(self):
        d = tempfile.mkdtemp()
        vault = Vault.init(d)
        commands.write_builtin_types(vault)
        yield vault
        shutil.rmtree(d)

    @pytest.fixture
    def repl(self, vault):
        return Repl(vault=vault)

    def test_new_creates_node(self, repl, capsys):
        repl._handle_line("new note TestNote --tag test")
        captured = capsys.readouterr()
        assert "Created note node:" in captured.out
        assert repl.last_uuid is not None

    def test_show_node(self, repl, capsys):
        repl._handle_line("new note ShowTest")
        uid = repl.last_uuid
        repl._handle_line(f"show {uid}")
        captured = capsys.readouterr()
        assert "ShowTest" in captured.out

    def test_underscore_resolves_to_last_uuid(self, repl, capsys):
        repl._handle_line("new note FirstNode")
        assert repl.last_uuid is not None
        repl._handle_line("show _")
        captured = capsys.readouterr()
        assert "FirstNode" in captured.out

    def test_aliases_dispatch_to_correct_commands(self, repl, capsys):
        repl._handle_line("n note AliasTest --tag alias-test")
        captured = capsys.readouterr()
        assert "Created note node:" in captured.out
        assert repl.last_uuid is not None

    def test_query_returns_results(self, repl, capsys):
        repl._handle_line("new note QueryTest --tag query-tag")
        repl._handle_line("query tag:query-tag")
        captured = capsys.readouterr()
        assert "QueryTest" in captured.out

    def test_help_with_command(self, repl, capsys):
        repl._handle_line("help new")
        captured = capsys.readouterr()
        assert "Create a new typed node" in captured.out

    def test_unknown_command(self, repl, capsys):
        repl._handle_line("nonexistent")
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_history_does_not_raise(self, repl):
        import readline
        readline.add_history("test command")
        repl._handle_line("history")

    def test_init_from_full_mode(self, repl):
        d = tempfile.mkdtemp()
        try:
            repl._handle_line(f"init {d}")
            assert repl.vault is not None
        finally:
            shutil.rmtree(d)

    def test_open_from_full_mode(self, repl, vault):
        old_uuid = vault.vault_uuid
        repl._handle_line(f"open {vault.path}")
        assert repl.vault is not None
        assert repl.vault.vault_uuid == old_uuid

    def test_link_command(self, repl, capsys):
        repl._handle_line("new note SourceNode")
        src_uuid = repl.last_uuid
        repl._handle_line("new note TargetNode")
        tgt_uuid = repl.last_uuid
        repl._handle_line(f"link {src_uuid} {tgt_uuid}")
        captured = capsys.readouterr()
        assert "Linked" in captured.out

    def test_tag_add_command(self, repl, capsys):
        repl._handle_line("new note TagTest --tag work")
        uid = repl.last_uuid
        repl._handle_line(f"tag add {uid} personal")
        captured = capsys.readouterr()
        assert "Added tag: personal" in captured.out

    def test_tag_rm_command(self, repl, capsys):
        repl._handle_line("new note TagRmTest --tag work")
        uid = repl.last_uuid
        repl._handle_line(f"tag rm {uid} work")
        captured = capsys.readouterr()
        assert "Removed tag: work" in captured.out

    def test_tag_list_command(self, repl, capsys):
        repl._handle_line("new note TagListTest --tag work")
        repl._handle_line("tag list")
        captured = capsys.readouterr()
        assert "work" in captured.out

    def test_tag_list_count_command(self, repl, capsys):
        repl._handle_line("new note TagCountTest --tag work")
        repl._handle_line("tag list --count")
        captured = capsys.readouterr()
        assert "work (1)" in captured.out

    def test_tag_rename_command(self, repl, capsys):
        repl._handle_line("new note TagRenameTest --tag work")
        repl._handle_line("tag rename work tasks")
        captured = capsys.readouterr()
        assert "Renamed tag" in captured.out

    def test_tag_help(self, repl, capsys):
        repl._handle_line("help tag")
        captured = capsys.readouterr()
        assert "manage tags" in captured.out.lower()

    def test_backlinks_command(self, repl, capsys):
        repl._handle_line("new note BLSource")
        repl._handle_line("new note BLTarget")
        tgt = repl.last_uuid
        repl._handle_line("new note BLSrc2")
        src = repl.last_uuid
        repl._handle_line(f"link {src} {tgt}")
        repl._handle_line(f"backlinks {tgt}")
        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestReplCompletion:
    def test_command_completion_partial(self):
        cmds = completions.complete_command("n", ALIASES)
        assert "n" in cmds
        assert "new" in cmds

    def test_command_completion_empty(self):
        cmds = completions.complete_command("", ALIASES)
        assert "new" in cmds
        assert "help" in cmds
        assert "exit" in cmds

    def test_uuid_completion(self):
        d = tempfile.mkdtemp()
        try:
            vault = Vault.init(d)
            commands.write_builtin_types(vault)
            repl = Repl(vault=vault)
            repl._handle_line("new note UUIDComplete")
            uid = repl.last_uuid
            assert uid is not None
            matches = completions.complete_uuid(vault, uid[:8])
            assert any(uid in m for m in matches)
        finally:
            shutil.rmtree(d)

    def test_type_name_completion(self):
        d = tempfile.mkdtemp()
        try:
            vault = Vault.init(d)
            commands.write_builtin_types(vault)
            names = completions.complete_type_name(vault, "n")
            assert "note" in names
        finally:
            shutil.rmtree(d)

    def test_uuid_completion_no_vault_returns_empty(self):
        assert completions.complete_uuid(None, "") == []

    def test_type_name_completion_no_vault_returns_empty(self):
        assert completions.complete_type_name(None, "") == []

    def test_tag_completion(self):
        d = tempfile.mkdtemp()
        try:
            vault = Vault.init(d)
            commands.write_builtin_types(vault)
            repl = Repl(vault=vault)
            repl._handle_line("new note TagTest --tag hello-tag")
            tags = completions.complete_tag(vault, "hel")
            assert "hello-tag" in tags
        finally:
            shutil.rmtree(d)
