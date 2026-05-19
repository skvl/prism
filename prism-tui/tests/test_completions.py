from __future__ import annotations

import os
import tempfile

from prism_tui.widgets.completions import FilesystemCompleter


def _assert_paths_equal(result: list[str], expected: list[str]) -> None:
    """Compare paths using normpath to handle symlinks, trailing slashes etc."""
    assert [os.path.normpath(p) for p in result] == [os.path.normpath(p) for p in expected]


def test_completer_single_match() -> None:
    """Completing a unique prefix returns that single path."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "myvault"))
        os.makedirs(os.path.join(tmp, "other"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "my"))
        assert result == [os.path.join(tmp, "myvault") + "/"]


def test_completer_multiple_matches() -> None:
    """Completing an ambiguous prefix returns all matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "al"))
        assert len(result) == 2
        assert all(r.startswith(os.path.join(tmp, "al")) for r in result)


def test_completer_no_match_returns_empty() -> None:
    """Completing a prefix with no matches returns empty list."""
    with tempfile.TemporaryDirectory() as tmp:
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "nonexistent"))
        assert result == []


def test_completer_expands_tilde() -> None:
    """Completer should expand ~ to home directory."""
    completer = FilesystemCompleter()
    home = os.path.expanduser("~")
    result = completer.complete("~")
    # Should return something under home
    assert any(r.startswith(home) for r in result)


def test_completer_appends_trailing_slash_for_dirs() -> None:
    """Completer should add trailing / for directory matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "adir"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "ad"))
        assert result[0].endswith("/")


def test_completer_hides_hidden_files_by_default() -> None:
    """Completer should not show hidden files when prefix doesn't start with dot."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".hidden"))
        os.makedirs(os.path.join(tmp, "visible"))
        completer = FilesystemCompleter()
        result = completer.complete(tmp + "/")
        names = [os.path.basename(p.rstrip("/")) for p in result]
        assert all(not n.startswith(".") for n in names)
        assert "visible" in names


def test_completer_shows_hidden_files_when_prefix_starts_with_dot() -> None:
    """Completer should show hidden files when prefix starts with dot."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".hidden"))
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, ".h"))
        names = [os.path.basename(p.rstrip("/")) for p in result]
        assert ".hidden" in names


def test_completer_relative_path_has_no_dot_prefix() -> None:
    """Completing a relative path like 'myvault' should not produce './myvault/'."""
    with tempfile.TemporaryDirectory() as tmp:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp)
            os.makedirs("myvault")
            completer = FilesystemCompleter()
            result = completer.complete("my")
            assert result == ["myvault/"]
        finally:
            os.chdir(original_cwd)


def test_completer_expands_tilde_specific_path() -> None:
    """Completer should expand ~/ effectively."""
    completer = FilesystemCompleter()
    home = os.path.expanduser("~/")
    result = completer.complete("~")
    assert len(result) > 0
    assert all(r.startswith(os.path.expanduser("~")) for r in result[:5])


def test_completer_oserror_returns_empty() -> None:
    """Completer should return empty list on OSError."""
    completer = FilesystemCompleter()
    result = completer.complete("/NONEXISTENT_DIR_XYZ/")
    assert result == []


def test_completer_matches_files_with_extension() -> None:
    """Completer should find files as well as directories."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "testfile.txt"), "w") as f:
            f.write("hello")
        completer = FilesystemCompleter()
        result = completer.complete(os.path.join(tmp, "testfile"))
        assert any("testfile.txt" in r for r in result)
