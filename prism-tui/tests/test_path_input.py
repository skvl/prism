from __future__ import annotations

import os
import tempfile

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input

from prism_tui.widgets.path_input import PathInput


class _PathInputHarness(App[None]):
    """Test harness that mounts a PathInput."""

    def compose(self) -> ComposeResult:
        yield PathInput(id="test-path-input")


@pytest.mark.asyncio
async def test_path_input_is_path_input() -> None:
    """PathInput should be a PathInput widget."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        assert isinstance(pi, PathInput)


@pytest.mark.asyncio
async def test_path_input_value_property() -> None:
    """PathInput should expose value property like Input."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        pi.value = "/tmp/test"
        assert pi.value == "/tmp/test"


@pytest.mark.asyncio
async def test_tab_completes_single_match() -> None:
    """TAB on a unique prefix should complete the path inline."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "myvault"))
        os.makedirs(os.path.join(tmp, "other"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "my")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            expected = os.path.join(tmp, "myvault") + "/"
            assert pi.value == expected


@pytest.mark.asyncio
async def test_tab_with_empty_input_does_not_complete() -> None:
    """TAB with empty input should not affect the value."""
    app = _PathInputHarness()
    async with app.run_test() as pilot:
        await pilot.pause()
        pi = app.screen.query_one("#test-path-input", PathInput)
        assert pi.value == ""
        await pilot.press("tab")
        await pilot.pause()
        assert pi.value == ""


@pytest.mark.asyncio
async def test_tab_with_multiple_matches_shows_popup() -> None:
    """TAB with multiple matches should show completion popup."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            # Popup should be visible
            assert pi._popup is not None


@pytest.mark.asyncio
async def test_tab_cycles_through_matches() -> None:
    """Repeated TAB should cycle through multiple matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            first_value = pi.value
            await pilot.press("tab")
            await pilot.pause()
            second_value = pi.value
            assert first_value != second_value


@pytest.mark.asyncio
async def test_escape_dismisses_popup() -> None:
    """ESC should dismiss the completion popup."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            await pilot.press("tab")
            await pilot.pause()
            assert pi._popup is not None
            await pilot.press("escape")
            await pilot.pause()
            assert pi._popup is None


@pytest.mark.asyncio
async def test_typing_dismisses_popup() -> None:
    """Typing a character should dismiss the popup."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            await pilot.press("tab")
            await pilot.pause()
            assert pi._popup is not None
            await pilot.press("x")
            await pilot.pause()
            assert pi._popup is None


@pytest.mark.asyncio
async def test_cycling_updates_popup_highlight() -> None:
    """TAB cycling should update the popup's highlighted index."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        os.makedirs(os.path.join(tmp, "alright"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            assert pi._popup is not None
            initial_index = pi._popup.index
            await pilot.press("tab")
            await pilot.pause()
            assert pi._popup.index != initial_index


@pytest.mark.asyncio
async def test_cycling_wraps_around() -> None:
    """TAB cycling should wrap from last match back to first."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            pi.cursor_position = len(pi.value)
            await pilot.press("tab")
            await pilot.pause()
            first_value = pi.value
            await pilot.press("tab")
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            assert pi.value == first_value


@pytest.mark.asyncio
async def test_typing_dismisses_after_cycling() -> None:
    """Typing should dismiss popup even after cycling through matches."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "alpha"))
        os.makedirs(os.path.join(tmp, "alpine"))
        app = _PathInputHarness()
        async with app.run_test() as pilot:
            await pilot.pause()
            pi = app.screen.query_one("#test-path-input", PathInput)
            pi.value = os.path.join(tmp, "al")
            await pilot.press("tab")
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()
            assert pi._popup is not None
            await pilot.press("x")
            await pilot.pause()
            assert pi._popup is None
