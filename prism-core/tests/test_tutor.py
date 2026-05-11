import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from prism.node.manager import NodeManager
from prism.node.metadata import NodeMetadata
from prism.node.storage import compute_storage_path, sha256_file
from prism.vault.vault import Vault

from prism_cli.tutor import Lesson, Step, StepResult, TOTAL_LESSONS, Tutor
from prism_cli.main import _write_builtin_types


class TestDataModel:
    def test_step_creation(self):
        step = Step(number=1, concept="test", command="prism init .", verify=lambda v: True)
        assert step.number == 1
        assert step.concept == "test"
        assert step.command == "prism init ."
        assert step.verify is not None
        assert step.warning == ""

    def test_step_with_warning(self):
        step = Step(number=2, concept="test", command="prism status",
                    verify=lambda v: True, warning="Pay attention")
        assert step.warning == "Pay attention"

    def test_lesson_creation(self):
        steps = [
            Step(number=1, concept="s1", command="c1", verify=lambda v: True),
            Step(number=2, concept="s2", command="c2", verify=lambda v: True),
        ]
        lesson = Lesson(number=1, title="Test Lesson", concept="A test", steps=steps, summary="Done")
        assert lesson.number == 1
        assert lesson.title == "Test Lesson"
        assert len(lesson.steps) == 2
        assert lesson.summary == "Done"

    def test_lesson_default_summary(self):
        lesson = Lesson(number=1, title="Test", concept="Test", steps=[])
        assert lesson.summary == ""

    def test_step_result_values(self):
        assert StepResult.SUCCESS.value == "success"
        assert StepResult.WARNING_RETRY.value == "warning_retry"
        assert StepResult.SKIP.value == "skip"


class TestVerifyHelpers:
    @pytest.fixture
    def tutor_with_vault(self):
        t = Tutor()
        t.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-test-")
        vault = Vault.init(t.temp_dir)
        _write_builtin_types(vault)
        t.vault = vault
        yield t
        shutil.rmtree(t.temp_dir)

    def test_verify_vault_init(self, tutor_with_vault):
        assert tutor_with_vault._verify_vault_init(tutor_with_vault.vault)

    def test_verify_node_count(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        assert tutor_with_vault._verify_node_count(vault, 0, "note")
        manager = NodeManager(vault.path)
        manager.create_node(type_name="note", title="Test")
        assert tutor_with_vault._verify_node_count(vault, 1, "note")

    def test_verify_node_has_tag(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Test", tags=["ideas"])
        assert tutor_with_vault._verify_node_has_tag(vault, meta.uuid, "ideas")
        assert not tutor_with_vault._verify_node_has_tag(vault, meta.uuid, "work")

    def test_verify_link_exists(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        manager = NodeManager(vault.path)
        n1 = manager.create_node(type_name="note", title="Note 1")
        n2 = manager.create_node(type_name="note", title="Note 2")
        storage_dir = compute_storage_path(vault.path, n1.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta = NodeMetadata.from_toml(meta_path)
        meta.links.append({"target": n2.uuid[:8], "type": "note", "title": "Note 2"})
        meta.save(meta_path)
        assert tutor_with_vault._verify_link_exists(vault, n1.uuid, n2.uuid[:8])

    def test_verify_file_imported(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        manager = NodeManager(vault.path)
        file_path = os.path.join(tutor_with_vault.temp_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello")
        file_hash = sha256_file(file_path)
        manager.create_node(type_name="file", title="test.txt", blob_path=file_path)
        assert tutor_with_vault._verify_file_imported(vault, file_hash)

    def test_verify_change_detected_no_changes(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        assert not tutor_with_vault._verify_change_detected(vault)

    def test_verify_change_detected_with_change(self, tutor_with_vault):
        vault = tutor_with_vault.vault
        manager = NodeManager(vault.path)
        meta = manager.create_node(type_name="note", title="Test")
        storage_dir = compute_storage_path(vault.path, meta.uuid)
        meta_path = NodeMetadata.metadata_path(storage_dir)
        meta_loaded = NodeMetadata.from_toml(meta_path)
        meta_loaded.blob_mtime = str(os.stat(os.path.join(storage_dir, "data.md")).st_mtime)
        meta_loaded.save(meta_path)
        body_path = os.path.join(storage_dir, "data.md")
        with open(body_path, "w") as f:
            f.write("# changed")
        assert tutor_with_vault._verify_change_detected(vault)

    def test_verify_always_true(self, tutor_with_vault):
        assert tutor_with_vault._verify_always_true(tutor_with_vault.vault)


class TestExecuteCommand:
    @pytest.fixture
    def tutor(self):
        t = Tutor()
        t.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-test-")
        yield t
        shutil.rmtree(t.temp_dir)

    def test_execute_echo(self, tutor):
        result = tutor._execute_command("echo hello")
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_execute_failure(self, tutor):
        result = tutor._execute_command("false")
        assert result.returncode != 0


class TestBuildLessonPlan:
    def test_returns_7_lessons(self):
        t = Tutor()
        lessons = t._build_lesson_plan()
        assert len(lessons) == 7

    def test_lesson_numbers(self):
        t = Tutor()
        lessons = t._build_lesson_plan()
        for i, lesson in enumerate(lessons, 1):
            assert lesson.number == i

    def test_each_lesson_has_steps(self):
        t = Tutor()
        lessons = t._build_lesson_plan()
        for lesson in lessons:
            assert len(lesson.steps) >= 2


class TestTutorRun:
    @pytest.fixture
    def fresh_tutor(self):
        t = Tutor()
        yield t
        if t.temp_dir and os.path.exists(t.temp_dir):
            shutil.rmtree(t.temp_dir)

    def test_invalid_lesson_falls_back(self, fresh_tutor):
        fresh_tutor.lesson_number = 99
        with patch("builtins.input", return_value="n"):
            fresh_tutor.run()
        assert fresh_tutor.lesson_number == 1

    def test_creates_and_cleans_temp_dir(self, fresh_tutor):
        assert fresh_tutor.temp_dir == ""
        with patch("builtins.input", return_value="n"):
            fresh_tutor.run()
        assert fresh_tutor.temp_dir != ""
        assert not os.path.exists(fresh_tutor.temp_dir)


class TestCleanup:
    @pytest.fixture
    def tutor(self):
        t = Tutor()
        t.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-test-")
        vault = Vault.init(t.temp_dir)
        t.vault = vault
        yield t

    def test_discard(self, tutor):
        temp_dir = tutor.temp_dir
        assert os.path.exists(temp_dir)
        tutor._cleanup(keep=False)
        assert not os.path.exists(temp_dir)

    def test_keep(self, tutor, capsys):
        temp_dir = tutor.temp_dir
        tutor._cleanup(keep=True)
        assert os.path.exists(temp_dir)
        captured = capsys.readouterr()
        assert "Vault saved at" in captured.out


class TestUuidCapture:
    def test_capture_by_title(self):
        t = Tutor()
        t.temp_dir = tempfile.mkdtemp(prefix="prism-tutor-test-")
        try:
            vault = Vault.init(t.temp_dir)
            _write_builtin_types(vault)
            t.vault = vault
            manager = NodeManager(vault.path)
            meta = manager.create_node(type_name="note", title="My note")
            t._capture_uuid("My note", "testkey")
            assert t._fmt["testkey"] == meta.uuid[:8]
            assert t._fmt["_full_testkey"] == meta.uuid
        finally:
            shutil.rmtree(t.temp_dir)

    def test_resolve_uuid(self):
        t = Tutor()
        t._fmt = {"x": "abc12345", "_full_x": "abc12345-0000-0000-0000-000000000000"}
        assert t._resolve_uuid("x") == "abc12345-0000-0000-0000-000000000000"
        assert t._resolve_uuid("nonexistent") == "nonexistent"


class TestShowOutput:
    def test_shows_non_empty_lines(self, capsys):
        t = Tutor()
        t._show_output("hello\nworld")
        captured = capsys.readouterr()
        assert "  -> hello" in captured.out
        assert "  -> world" in captured.out

    def test_shows_nothing_for_empty(self, capsys):
        t = Tutor()
        t._show_output("")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_shows_nothing_for_whitespace(self, capsys):
        t = Tutor()
        t._show_output("  \n  \n")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_skips_empty_lines_between_content(self, capsys):
        t = Tutor()
        t._show_output("line1\n\n\nline2")
        captured = capsys.readouterr()
        assert "  -> line1" in captured.out
        assert "  -> line2" in captured.out
        # blank lines between should not have -> prefixes
        lines = [l for l in captured.out.split("\n") if "->" in l]
        assert len(lines) == 2
