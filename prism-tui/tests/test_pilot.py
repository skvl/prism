"""Textual pilot tests for tab switching and column browser interaction."""

from __future__ import annotations

import pytest
from prism.vault.vault import Vault
from textual.widgets import Input, Markdown, TabbedContent

from prism_tui.app import PrismTui
from prism_tui.tabs.browser import BrowserTab


@pytest.fixture
def vault(tmp_path) -> Vault:
    """Create a real vault for integration testing."""
    return Vault.init(str(tmp_path / "vault"))


@pytest.mark.asyncio
async def test_app_starts_with_browser_tab(vault: Vault) -> None:
    """App should start with the Browser tab active."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tab_container = app.query_one("#tab-container", TabbedContent)
        assert tab_container.active == "tab-browser"


@pytest.mark.asyncio
async def test_tab_switching(vault: Vault) -> None:
    """Should be able to switch between all four tabs."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tab_container = app.query_one("#tab-container", TabbedContent)

        assert tab_container.active == "tab-browser"

        tab_container.active = "tab-graph"
        await pilot.pause()
        assert tab_container.active == "tab-graph"

        tab_container.active = "tab-tags"
        await pilot.pause()
        assert tab_container.active == "tab-tags"

        tab_container.active = "tab-query"
        await pilot.pause()
        assert tab_container.active == "tab-query"

        tab_container.active = "tab-browser"
        await pilot.pause()
        assert tab_container.active == "tab-browser"


@pytest.mark.asyncio
async def test_switch_to_graph_tab_and_back(vault: Vault) -> None:
    """Switching to graph tab then back to browser should work."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tab_container = app.query_one("#tab-container", TabbedContent)

        tab_container.active = "tab-graph"
        await pilot.pause()
        assert tab_container.active == "tab-graph"

        tab_container.active = "tab-browser"
        await pilot.pause()
        assert tab_container.active == "tab-browser"


@pytest.mark.asyncio
async def test_switch_to_tag_cloud_tab(vault: Vault) -> None:
    """Switching to Tag Cloud tab should work."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tab_container = app.query_one("#tab-container", TabbedContent)

        tab_container.active = "tab-tags"
        await pilot.pause()
        assert tab_container.active == "tab-tags"


@pytest.mark.asyncio
async def test_switch_to_query_tab(vault: Vault) -> None:
    """Switching to Query tab should work."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        tab_container = app.query_one("#tab-container", TabbedContent)

        tab_container.active = "tab-query"
        await pilot.pause()
        assert tab_container.active == "tab-query"


@pytest.mark.asyncio
async def test_browser_tab_has_three_columns(vault: Vault) -> None:
    """Browser tab should render three columns with headers."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        browser = app.query_one(BrowserTab)

        assert browser.query_one("#path-column") is not None
        assert browser.query_one("#node-column") is not None
        assert browser.query_one("#preview-column") is not None

        headers = browser.query(".column-header")
        header_texts = [h.content for h in headers]
        assert "Paths" in header_texts
        assert "Nodes" in header_texts
        assert "Preview" in header_texts

        assert browser.query_one("#path-tree") is not None
        assert browser.query_one("#node-list") is not None
        assert browser.query_one("#preview-content") is not None


@pytest.mark.asyncio
async def test_browser_tab_loads_with_vault(vault: Vault) -> None:
    """Browser tab should load data from the vault on mount."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        browser = app.query_one(BrowserTab)

        assert browser._vault is vault
        assert browser._manager is not None
        assert browser._resolver is not None


@pytest.mark.asyncio
async def test_colon_via_shift_semicolon_enters_command_mode(vault: Vault) -> None:
    """Pressing shift+semicolon should show the command Input and focus it."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        cmd_input = app.query_one("#command-input", Input)
        assert not cmd_input.has_class("-active")

        await pilot.press("shift+semicolon")
        await pilot.pause()

        assert cmd_input.has_class("-active")
        assert app.focused is cmd_input


@pytest.mark.asyncio
async def test_colon_via_action_enter_command_mode(vault: Vault) -> None:
    """action_enter_command_mode should show the command Input and focus it."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        cmd_input = app.query_one("#command-input", Input)
        assert not cmd_input.has_class("-active")

        app.action_enter_command_mode()
        await pilot.pause()

        assert cmd_input.has_class("-active")
        assert app.focused is cmd_input


@pytest.mark.asyncio
async def test_escape_exits_command_mode(vault: Vault) -> None:
    """Pressing Esc in command mode should hide the Input."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        cmd_input = app.query_one("#command-input", Input)
        await pilot.press("shift+semicolon")
        await pilot.pause()
        assert cmd_input.has_class("-active")

        await pilot.press("escape")
        await pilot.pause()
        assert not cmd_input.has_class("-active")


@pytest.mark.asyncio
async def test_command_input_submit_executes_new_wizard(vault: Vault) -> None:
    """Submitting :new in command input should open NewNodeWizard."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        await pilot.press("shift+semicolon")
        await pilot.pause()

        cmd_input = app.query_one("#command-input", Input)
        cmd_input.value = "new"
        await pilot.press("enter")
        await pilot.pause()

        stacked_screens = app.screen_stack
        assert len(stacked_screens) >= 2


@pytest.mark.asyncio
async def test_q_does_not_quit_when_focused_in_input(vault: Vault) -> None:
    """Pressing q should not quit when an Input widget is focused."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        cmd_input = app.query_one("#command-input", Input)
        cmd_input.add_class("-active")
        cmd_input.focus()
        await pilot.pause()

        await pilot.press("q")
        await pilot.pause()

        assert app.is_running


@pytest.mark.asyncio
async def test_f2_opens_new_node_wizard(vault: Vault) -> None:
    """Pressing F2 should open the new node wizard."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        await pilot.press("f2")
        await pilot.pause()

        stacked_screens = app.screen_stack
        assert len(stacked_screens) >= 2


@pytest.mark.asyncio
async def test_empty_vault_shows_welcome_message(vault: Vault) -> None:
    """Empty vault should show a welcome message in the preview panel."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        preview = app.query_one("#preview-content", Markdown)
        assert preview is not None


@pytest.mark.asyncio
async def test_empty_vault_path_tree_shows_root(vault: Vault) -> None:
    """Empty vault path tree should show the root / entry."""
    app = PrismTui(vault=vault)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()

        browser = app.query_one(BrowserTab)
        tree = browser.query_one("#path-tree")
        assert tree is not None
        assert str(tree.root.label) == "/"
