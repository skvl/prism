from __future__ import annotations

import os
import tempfile

from prism_tui.widgets.completions import FilesystemCompleter


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
