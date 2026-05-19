from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from prism_tui.command_mode import execute_command


def test_execute_command_new_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    result = execute_command('new note "My Title" --tag work', vault, notify, push_screen)
    assert result is not None
    assert not push_screen.called


def test_execute_command_link_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    result = execute_command("link src-uuid dst-uuid", vault, notify, push_screen)
    assert result is not None
    assert not push_screen.called


def test_execute_command_tag_with_args():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    result = execute_command("tag node-uuid work important", vault, notify, push_screen)
    assert result is not None
    assert not push_screen.called


def test_execute_command_quit():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with patch("textual.app.App") as MockApp:
        mock_app = MagicMock()
        MockApp.running_app = mock_app
        execute_command("quit", vault, notify, push_screen)
        assert mock_app.exit.called


def test_execute_command_exit():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with patch("textual.app.App") as MockApp:
        mock_app = MagicMock()
        MockApp.running_app = mock_app
        execute_command("exit", vault, notify, push_screen)
        assert mock_app.exit.called


def test_execute_command_q():
    vault = MagicMock()
    notify = MagicMock()
    push_screen = MagicMock()
    with patch("textual.app.App") as MockApp:
        mock_app = MagicMock()
        MockApp.running_app = mock_app
        execute_command("q", vault, notify, push_screen)
        assert mock_app.exit.called
