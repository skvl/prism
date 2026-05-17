"""Tests for command dispatch logic."""

from unittest.mock import MagicMock

from prism_tui.command_mode import execute_command


def _make_notify() -> MagicMock:
    return MagicMock()


def test_unknown_command_returns_error() -> None:
    vault = MagicMock()
    notify = _make_notify()
    result = execute_command("invalidcmd", vault, notify, MagicMock())
    assert result is not None
    assert "Unknown command" in result


def test_help_command() -> None:
    vault = MagicMock()
    notify = _make_notify()
    result = execute_command("help", vault, notify, MagicMock())
    assert result is not None
    assert "Commands:" in result


def test_new_command_without_args_opens_wizard() -> None:
    vault = MagicMock()
    notify = _make_notify()
    push_screen = MagicMock()
    result = execute_command("new", vault, notify, push_screen)
    assert result is None
    assert push_screen.called


def test_link_command_without_args_opens_wizard() -> None:
    vault = MagicMock()
    notify = _make_notify()
    push_screen = MagicMock()
    result = execute_command("link", vault, notify, push_screen)
    assert result is None
    assert push_screen.called


def test_empty_command_returns_none() -> None:
    vault = MagicMock()
    notify = _make_notify()
    result = execute_command("", vault, notify, MagicMock())
    assert result is None
