import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

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


# ── Verify Description ──────────────────────────────────────────────────


class TestVerifyDescription:
    def test_description_present(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(
            type_name="note", title="Has Desc", description="A meaningful summary"
        )
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_description(vault, meta.uuid, "A meaningful summary") is True

    def test_description_absent(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="No Desc")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_description(vault, meta.uuid, "anything") is False

    def test_description_wrong_content(self, vault):
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Wrong Desc", description="Wrong text")
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._verify_description(vault, meta.uuid, "Expected text") is False


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


# ── Show Output ──────────────────────────────────────────────────────────


class TestShowOutput:
    def test_show_output(self, capsys):
        tutor = Tutor()
        tutor._show_output("hello world")
        captured = capsys.readouterr()
        assert "-> hello world" in captured.out

    def test_show_output_empty(self, capsys):
        tutor = Tutor()
        tutor._show_output("")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_show_output_multiline(self, capsys):
        tutor = Tutor()
        tutor._show_output("line1\nline2")
        captured = capsys.readouterr()
        assert "-> line1" in captured.out
        assert "-> line2" in captured.out


# ── Show Success ─────────────────────────────────────────────────────────


class TestShowSuccess:
    def test_show_success(self, capsys):
        tutor = Tutor()
        tutor._show_success("Step complete!")
        captured = capsys.readouterr()
        assert "OK Step complete!" in captured.out


# ── Execute Command ─────────────────────────────────────────────────────


class TestExecuteCommand:
    def test_execute_echo(self, vault_dir):
        tutor = Tutor()
        tutor.temp_dir = vault_dir
        result = tutor._execute_command("echo hello")
        assert result.returncode == 0
        assert result.stdout.strip() == "hello"

    def test_execute_failure(self, vault_dir):
        tutor = Tutor()
        tutor.temp_dir = vault_dir
        result = tutor._execute_command("false")
        assert result.returncode != 0


# ── Build Lesson Plan ────────────────────────────────────────────────────


class TestBuildLessonPlan:
    def test_eight_lessons(self):
        from prism_cli.tutor import Lesson

        tutor = Tutor()
        lessons = tutor._build_lesson_plan()
        assert len(lessons) == 8
        for lesson in lessons:
            assert isinstance(lesson, Lesson)
            assert len(lesson.steps) >= 1

    def test_lesson_numbering(self):
        tutor = Tutor()
        lessons = tutor._build_lesson_plan()
        for i, lesson in enumerate(lessons, 1):
            assert lesson.number == i


# ── Get Node UUID By Title ───────────────────────────────────────────────


class TestGetNodeUUIDByTitle:
    def test_not_found(self, vault):
        tutor = Tutor()
        tutor.vault = vault
        assert tutor._get_node_uuid_by_title(vault, "NonExistent") is None


# ── Tutor Lifecycle ──


class TestTutorLifecycle:
    def test_create_temp_vault(self, tutor):
        tutor._create_temp_vault()
        assert tutor.temp_dir != ""
        assert os.path.exists(tutor.temp_dir)

    def test_ensure_vault_open_when_not_initialized(self, tutor):
        tutor._create_temp_vault()
        result = tutor._ensure_vault_open()
        assert result is None

    def test_write_builtin_types(self, vault_dir):
        from prism.vault.vault import Vault

        vault = Vault.open(vault_dir)
        tutor = Tutor()
        tutor._write_builtin_types(vault)
        types_dir = os.path.join(vault_dir, ".metadata", "types")
        assert os.path.exists(os.path.join(types_dir, "note.toml"))
        assert os.path.exists(os.path.join(types_dir, "contact.toml"))

    def test_cleanup_keep(self, tutor):
        tutor._create_temp_vault()
        vault_path = tutor.temp_dir
        tutor._cleanup(keep=True)
        assert os.path.exists(vault_path)

    def test_cleanup_remove(self, tutor):
        tutor._create_temp_vault()
        vault_path = tutor.temp_dir
        tutor._cleanup(keep=False)
        assert not os.path.exists(vault_path)


# ── Output Rendering ──


class TestTutorOutput:
    def test_show_header_output(self, capsys, tutor):
        tutor._show_header(1, "Test", 8)
        captured = capsys.readouterr()
        assert "Lesson 1/8: Test" in captured.out

    def test_show_concept_output(self, capsys, tutor):
        tutor._show_concept("Hello world")
        captured = capsys.readouterr()
        assert "Hello world" in captured.out

    def test_show_command_output(self, capsys, tutor):
        tutor._show_command("prism init .")
        captured = capsys.readouterr()
        assert "prism init ." in captured.out

    def test_show_success_output(self, capsys, tutor):
        tutor._show_success("Done!")
        captured = capsys.readouterr()
        assert "Done!" in captured.out

    def test_show_warning_output(self, capsys, tutor):
        tutor._show_warning("Oops!")
        captured = capsys.readouterr()
        assert "Oops!" in captured.out

    def test_show_progress_output(self, capsys, tutor):
        tutor._show_progress(1, 5)
        captured = capsys.readouterr()
        assert "Step 1/5" in captured.out

    def test_show_final_summary_output(self, capsys, tutor):
        tutor._show_final_summary()
        captured = capsys.readouterr()
        assert "Congratulations" in captured.out

    def test_show_auto_run_output(self, capsys, tutor):
        tutor._show_auto_run("prism init")
        captured = capsys.readouterr()
        assert "Auto-running" in captured.out

    def test_show_output_with_text(self, capsys, tutor):
        tutor._show_output("hello\nworld\n")
        captured = capsys.readouterr()
        assert "hello" in captured.out
        assert "world" in captured.out

    def test_show_output_empty(self, capsys, tutor):
        tutor._show_output("")
        captured = capsys.readouterr()
        assert captured.out == ""


# ── UUID Capture and Resolution ──


class TestTutorUuidCapture:
    def test_capture_uuid_no_vault(self, tutor):
        tutor.vault = None
        tutor._capture_uuid("test", "key1")
        assert "key1" not in tutor._fmt

    def test_resolve_uuid_returns_short_when_not_found(self, tutor):
        result = tutor._resolve_uuid("unknown")
        assert result == "unknown"

    def test_resolve_uuid_returns_full(self, tutor):
        tutor._fmt["_full_known"] = "full-uuid-value"
        result = tutor._resolve_uuid("known")
        assert result == "full-uuid-value"

    def test_build_prism_cmd(self, tutor):
        cmd = tutor._build_prism_cmd("prism init .")
        import sys

        assert cmd.startswith(sys.executable)
        assert "init" in cmd


# ── Lesson Plan Construction ──


class TestLessonPlan:
    def test_build_lesson_plan_returns_8_lessons(self, tutor):
        lessons = tutor._build_lesson_plan()
        assert len(lessons) == 8

    def test_each_lesson_has_steps(self, tutor):
        lessons = tutor._build_lesson_plan()
        for lesson in lessons:
            assert len(lesson.steps) >= 1

    def test_lessons_are_ordered(self, tutor):
        lessons = tutor._build_lesson_plan()
        for i, lesson in enumerate(lessons, 1):
            assert lesson.number == i


# ── Step Execution ──


class TestTutorStepExecution:
    def test_run_step_concept_display(self, capsys, tutor, vault_dir):
        from prism_cli.tutor import Step, StepResult

        tutor.temp_dir = vault_dir
        step = Step(
            number=1,
            concept="Test concept",
            command="echo hello",
            verify=lambda v: True,
        )
        with patch("builtins.input", return_value=""):
            result = tutor._run_step(step)
        assert result == StepResult.SUCCESS
        captured = capsys.readouterr()
        assert "Test concept" in captured.out

    def test_run_step_with_prism_command(self, capsys, tutor):
        from prism_cli.tutor import Step, StepResult

        tmp_dir = tempfile.mkdtemp()
        try:
            tutor.temp_dir = tmp_dir
            step = Step(
                number=1,
                concept="Init",
                command="prism init .",
                verify=lambda v: True,
            )
            with patch("builtins.input", return_value=""):
                result = tutor._run_step(step)
            assert result == StepResult.SUCCESS
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_run_step_command_fails_retry_skip(self, capsys, tutor, vault_dir):
        from prism_cli.tutor import Step, StepResult

        tutor.temp_dir = vault_dir
        step = Step(
            number=1,
            concept="Fail test",
            command="nonexistent_command_xyz",
            verify=lambda v: True,
        )
        with patch("builtins.input", side_effect=["", "n"]):
            result = tutor._run_step(step)
        assert result == StepResult.SKIP

    def test_run_step_verification_fails_retry_skip(self, capsys, tutor, vault_dir):
        from prism_cli.tutor import Step, StepResult

        tutor.temp_dir = vault_dir
        step = Step(
            number=1,
            concept="Verify fail",
            command="echo hello",
            verify=lambda v: False,
        )
        with patch("builtins.input", side_effect=["", "n"]):
            result = tutor._run_step(step)
        assert result == StepResult.SKIP

    def test_prompt_keep_vault_yes(self, tutor):
        with patch("builtins.input", return_value="y"):
            assert tutor._prompt_keep_vault() is True

    def test_prompt_keep_vault_no(self, tutor):
        with patch("builtins.input", return_value=""):
            assert tutor._prompt_keep_vault() is False

    def test_prompt_keep_vault_eof(self, tutor):
        with patch("builtins.input", side_effect=EOFError):
            assert tutor._prompt_keep_vault() is False

    def test_execute_command(self, tutor):
        tutor._create_temp_vault()
        result = tutor._execute_command("echo hello")
        assert result.returncode == 0
        assert "hello" in result.stdout


# ── Run Method ──


class TestTutorRun:
    def test_run_invalid_lesson_number(self, capsys, tutor):
        tutor.lesson_number = 99
        with patch("builtins.input", return_value=""):
            with patch.object(tutor, "_run_lesson", side_effect=KeyboardInterrupt):
                with pytest.raises(SystemExit):
                    tutor.run()
        captured = capsys.readouterr()
        assert "Starting from lesson 1" in captured.out

    def test_run_keyboard_interrupt(self, capsys, tutor):
        tutor._create_temp_vault = MagicMock(side_effect=KeyboardInterrupt)
        with pytest.raises(SystemExit):
            tutor.run()
        captured = capsys.readouterr()
        assert "Tutorial paused" in captured.out

    def test_write_to_note_body(self, tutor, vault_dir):
        from prism.node.manager import NodeManager
        from prism.vault.vault import Vault

        vault = Vault.open(vault_dir)
        tutor.vault = vault
        manager = NodeManager(vault.path)
        node = manager.create_node("note", title="TestNote")
        tutor._write_to_note_body("TestNote", "Hello World")
        desc = manager.get_description(node.uuid)
        assert desc is None  # description is different from body


# ── Verify Helpers ──


class TestTutorNewVerifyHelpers:
    def test_verify_always_true(self, tutor, vault):
        assert tutor._verify_always_true(vault) is True

    def test_verify_blob_integrity_no_meta(self, tutor, vault_dir):
        from prism.vault.vault import Vault

        vault = Vault.open(vault_dir)
        assert tutor._verify_blob_integrity(vault, "00000000-0000-0000-0000-000000000000") is False

    def test_verify_change_detected_clean(self, tutor, vault):
        assert tutor._verify_change_detected(vault) is False
