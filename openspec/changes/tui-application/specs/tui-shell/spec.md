## ADDED Requirements

### Requirement: App entry point

The system SHALL provide a `prism-tui` command (via `python -m prism_tui`) and a `prism tui` bridge in prism-cli that launches the TUI application.

#### Scenario: Launch with explicit vault
- **WHEN** user runs `prism-tui --vault /path/to/vault`
- **THEN** the system SHALL open the vault at the given path
- **THEN** the system SHALL display the TUI with the Column Browser tab active

#### Scenario: Launch without vault
- **WHEN** user runs `prism-tui` without `--vault`
- **THEN** the system SHALL display an init/open screen with two options: "Initialize new vault" and "Open existing vault"

#### Scenario: Launch via prism-cli bridge
- **WHEN** user runs `prism tui --vault /path/to/vault`
- **THEN** the system SHALL launch the TUI process with the vault path forwarded

### Requirement: Tab management

The system SHALL provide a 4-tab interface: Column Browser, Graph View, Tag Cloud, Query Builder.

#### Scenario: Switch between tabs
- **WHEN** user presses `Tab` or clicks a tab header
- **THEN** the system SHALL display the selected tab
- **THEN** the system SHALL preserve each tab's state when switching away and back

#### Scenario: Default tab on startup
- **WHEN** the TUI starts with a vault connected
- **THEN** the system SHALL display the Column Browser tab as the default active tab

### Requirement: MC-style command bar

The system SHALL display a command bar at the bottom of the screen with 8 action buttons labeled `F1`–`F8`.

#### Scenario: Command bar shows context-sensitive actions
- **WHEN** the Column Browser tab is active and focus is on the Nodes column
- **THEN** the command bar SHALL show: `1Help  2New  3Edit  4Link  5Tag  6Delete  7Refresh  8Menu`

#### Scenario: Command bar responds to F-keys or number keys
- **WHEN** user presses `F2` or `2` on the command bar
- **THEN** the system SHALL trigger the "New" action

### Requirement: Command mode (`:`)

The system SHALL provide a command mode activated by pressing `:` that opens an Input widget at the bottom of the screen.

#### Scenario: Enter command mode
- **WHEN** user presses `:` in navigation mode
- **THEN** the system SHALL display a command Input widget with `: ` prefix
- **THEN** the system SHALL focus the Input widget for text entry

#### Scenario: Execute inline command
- **WHEN** user types `:new note "Title" --tag work` and presses Enter
- **THEN** the system SHALL create a new node with the given parameters
- **THEN** the system SHALL reflect the result in the active tab

#### Scenario: Open wizard from command mode
- **WHEN** user types `:new` (without arguments) and presses Enter
- **THEN** the system SHALL open a New Node wizard modal

#### Scenario: Exit command mode
- **WHEN** user presses `Esc` while in command mode
- **THEN** the system SHALL close the command Input without executing

#### Scenario: Tab completion in command mode
- **WHEN** user types `:link ` and presses Tab
- **THEN** the system SHALL suggest matching UUIDs

### Requirement: Cross-tab navigation

The system SHALL support cross-tab navigation: non-browser tabs can select a node and switch focus to the Column Browser.

#### Scenario: Tag cloud selects node in browser
- **WHEN** user clicks a tag in the Tag Cloud to filter nodes, then selects a result
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select the chosen node in the Nodes column and show its preview

#### Scenario: Query builder opens result in browser
- **WHEN** user clicks a result row in the Query Builder
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select the chosen node in the Nodes column and show its preview

#### Scenario: Graph view opens node in browser
- **WHEN** user clicks a node in the Graph view
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select the chosen node in the Nodes column and show its preview

### Requirement: Vault init/open screen

The system SHALL display a startup screen when no vault is provided.

#### Scenario: Initialize new vault
- **WHEN** user selects "Initialize new vault" on the startup screen
- **THEN** the system SHALL prompt for a vault path
- **THEN** the system SHALL initialize the vault and enter the TUI

#### Scenario: Open existing vault
- **WHEN** user selects "Open existing vault" on the startup screen
- **THEN** the system SHALL prompt for a vault path
- **THEN** the system SHALL open the vault and enter the TUI

### Requirement: Error handling and notifications

The system SHALL display errors and notifications in a non-blocking notification widget.

#### Scenario: Command error notification
- **WHEN** a command fails (e.g., invalid UUID, vault error)
- **THEN** the system SHALL display an error notification at the top of the screen
- **THEN** the notification SHALL auto-dismiss after 5 seconds

#### Scenario: Success notification
- **WHEN** a node is created, edited, or deleted
- **THEN** the system SHALL display a brief success notification
