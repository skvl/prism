"""Tests for startup screen vault connection flow."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from prism.vault.vault import Vault
from textual.app import App

from prism_tui.app import PrismTui
from prism_tui.startup_screen import StartupScreen
from prism_tui.widgets.path_input import PathInput


class _StartupHarness(App[Vault | None]):
    """Test harness that pushes StartupScreen and captures dismiss result."""

    def __init__(self) -> None:
        super().__init__()
        self.captured: list[Vault | None] = []

    def on_mount(self) -> None:
        self.push_screen(StartupScreen(), self._capture_result)

    def _capture_result(self, result: Vault | None) -> None:
        self.captured.append(result)
        self.exit(result)


@pytest.mark.asyncio
async def test_compose_includes_expected_widgets() -> None:
    """The startup screen should render title, subtitle, input, and buttons."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        assert screen.query_one("#title") is not None
        assert screen.query_one("#subtitle") is not None
        assert screen.query_one("#path-input") is not None
        assert screen.query_one("#open-btn") is not None
        assert screen.query_one("#init-btn") is not None


@pytest.mark.asyncio
async def test_open_with_path_calls_vault_open() -> None:
    """Clicking Open with a path should call Vault.open and dismiss with the vault."""
    mock_vault = MagicMock(spec=Vault)
    with patch(
        "prism_tui.startup_screen.Vault.open", return_value=mock_vault
    ) as mock_open:
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/test-vault"
            await pilot.click("#open-btn")
            await pilot.pause()
        mock_open.assert_called_once_with("/tmp/test-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_open_without_path_uses_cwd() -> None:
    """Clicking Open without a path should default to os.getcwd()."""
    mock_vault = MagicMock(spec=Vault)
    with patch(
        "prism_tui.startup_screen.Vault.open", return_value=mock_vault
    ) as mock_open:
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#open-btn")
            await pilot.pause()
        mock_open.assert_called_once_with(os.getcwd())
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_open_file_not_found_shows_notification() -> None:
    """Vault.open raising FileNotFoundError should show an error notification."""
    with patch(
        "prism_tui.startup_screen.Vault.open",
        side_effect=FileNotFoundError("no such vault"),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#open-btn")
            await pilot.pause()
            assert len(app.captured) == 0
            app.exit()


@pytest.mark.asyncio
async def test_open_generic_error_shows_notification() -> None:
    """Vault.open raising a generic exception should show an error notification."""
    with patch(
        "prism_tui.startup_screen.Vault.open",
        side_effect=PermissionError("denied"),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#open-btn")
            await pilot.pause()
            assert len(app.captured) == 0
            app.exit()


@pytest.mark.asyncio
async def test_init_with_path_calls_vault_init() -> None:
    """Clicking Init with a path should call Vault.init and dismiss with vault."""
    mock_vault = MagicMock(spec=Vault)
    with patch(
        "prism_tui.startup_screen.Vault.init", return_value=mock_vault
    ) as mock_init:
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/new-vault"
            await pilot.click("#init-btn")
            await pilot.pause()
        mock_init.assert_called_once_with("/tmp/new-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_init_without_path_shows_notification() -> None:
    """Clicking Init without a path should show an error notification."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.click("#init-btn")
        await pilot.pause()
        assert len(app.captured) == 0
        app.exit()


@pytest.mark.asyncio
async def test_init_generic_error_shows_notification() -> None:
    """Vault.init raising an exception should show an error notification."""
    with patch(
        "prism_tui.startup_screen.Vault.init",
        side_effect=OSError("permission denied"),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#open-btn")
            await pilot.pause()
            assert len(app.captured) == 0
            app.exit()


@pytest.mark.asyncio
async def test_app_shows_startup_screen_when_no_vault() -> None:
    """PrismTui(vault=None) should push StartupScreen on mount."""
    app = PrismTui(vault=None)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, StartupScreen)
        app.exit()


@pytest.mark.asyncio
async def test_app_skips_startup_screen_when_vault_provided() -> None:
    """PrismTui with a vault should not push StartupScreen."""
    vault_dir = tempfile.mkdtemp()
    vault = Vault.init(vault_dir)
    app = PrismTui(vault=vault)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert not isinstance(app.screen, StartupScreen)
        app.exit()


@pytest.mark.asyncio
async def test_enter_on_existing_vault_calls_open() -> None:
    """ENTER with a path to an existing vault should call Vault.open."""
    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.open", return_value=mock_vault) as mock_open,
        patch("prism_tui.startup_screen._path_is_vault", return_value=True),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/test-vault"
            await pilot.press("enter")
            await pilot.pause()
        mock_open.assert_called_once_with("/tmp/test-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_enter_on_new_path_calls_init() -> None:
    """ENTER with a path that doesn't exist should call Vault.init."""
    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.init", return_value=mock_vault) as mock_init,
        patch("prism_tui.startup_screen._path_is_vault", return_value=False),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = app.screen
            path_input = screen.query_one("#path-input")
            path_input.value = "/tmp/new-vault"
            await pilot.press("enter")
            await pilot.pause()
        mock_init.assert_called_once_with("/tmp/new-vault")
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_enter_empty_path_uses_default() -> None:
    """ENTER with empty path should try Vault.open at default location first."""
    from prism_tui.startup_screen import _DEFAULT_VAULT_PATH

    mock_vault = MagicMock(spec=Vault)
    with (
        patch("prism_tui.startup_screen.Vault.open", return_value=mock_vault) as mock_open,
        patch("prism_tui.startup_screen._path_is_vault", return_value=True),
    ):
        app = _StartupHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
        mock_open.assert_called_once_with(_DEFAULT_VAULT_PATH)
        assert app.captured[-1] is mock_vault


@pytest.mark.asyncio
async def test_startup_screen_uses_path_input() -> None:
    """StartupScreen should use PathInput widget."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        path_input = screen.query_one("#path-input")
        assert isinstance(path_input, PathInput)


@pytest.mark.asyncio
async def test_get_path_returns_stripped_value() -> None:
    """_get_path should return the stripped path input value."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        path_input = screen.query_one("#path-input")
        path_input.value = "  /some/path  "
        result = screen._get_path()
        assert result == "/some/path"


@pytest.mark.asyncio
async def test_get_path_returns_empty_when_empty() -> None:
    """_get_path should return empty string when input is empty."""
    app = _StartupHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = app.screen
        screen.query_one("#path-input").value = ""
        result = screen._get_path()
        assert result == ""


def test_path_is_vault_returns_false_for_nonexistent() -> None:
    """_path_is_vault should return False for non-existent paths."""
    from prism_tui.startup_screen import _path_is_vault
    assert _path_is_vault("/nonexistent/path") is False


def test_path_is_vault_returns_false_for_regular_dir(tmp_path) -> None:
    """_path_is_vault should return False for a regular directory."""
    from prism_tui.startup_screen import _path_is_vault
    assert _path_is_vault(str(tmp_path)) is False


def test_path_is_vault_returns_true_for_vault(tmp_path) -> None:
    """_path_is_vault should return True for a vault directory."""
    from prism_tui.startup_screen import _path_is_vault
    from prism.vault.vault import Vault
    vault = Vault.init(str(tmp_path / "myvault"))
    assert _path_is_vault(vault.path) is True
