## Purpose

The repl-interface capability provides a persistent, stateful REPL session for the Prism CLI, reducing typing friction through aliases, tab completion, session memory, and command history.
## Requirements
### Requirement: REPL entry command

The system SHALL provide a `prism repl` command that enters an interactive REPL session.
The Repl class SHALL accept optional `input_stream` and `output_stream` parameters
(defaulting to `sys.stdin` and `sys.stdout`) for testability.

#### Scenario: Launch REPL inside a vault directory
- **WHEN** user runs `prism repl` inside a vault directory
- **THEN** the system SHALL detect the vault via context detection
- **THEN** the system SHALL display a welcome message with vault path
- **THEN** the system SHALL display a `prism> ` prompt and await input
- **THEN** the system SHALL restore command history from `~/.prism_repl_history`

#### Scenario: Launch REPL outside a vault (degraded mode)
- **WHEN** user runs `prism repl` outside any vault directory and without `--vault`
- **THEN** the system SHALL enter degraded mode
- **THEN** the system SHALL display a message that no vault is connected
- **THEN** the system SHALL allow only `init`, `open`, `help`, and `exit` commands

#### Scenario: Launch REPL with explicit vault
- **WHEN** user runs `prism repl --vault /path/to/vault`
- **THEN** the system SHALL connect to the specified vault
- **THEN** the system SHALL enter full REPL mode

#### Scenario: REPL with custom I/O streams (test mode)
- **WHEN** `Repl(input_stream=io.StringIO("exit\n"), output_stream=io.StringIO())` is constructed
- **THEN** the REPL SHALL read commands from `input_stream` and write output to `output_stream`
- **THEN** the REPL SHALL process the "exit" command and terminate
- **THEN** no output SHALL appear on stdout

### Requirement: Exit REPL

The system SHALL provide commands to exit the REPL session.

#### Scenario: Exit with exit command
- **WHEN** user types `exit` at the prompt
- **THEN** the system SHALL save history to `~/.prism_repl_history`
- **THEN** the system SHALL exit the REPL loop and return to shell

#### Scenario: Exit with quit command
- **WHEN** user types `quit` at the prompt
- **THEN** the system SHALL exit the REPL loop and return to shell

#### Scenario: Exit with Ctrl+D
- **WHEN** user presses Ctrl+D at the prompt
- **THEN** the system SHALL catch `EOFError`
- **THEN** the system SHALL exit the REPL loop and return to shell

### Requirement: Command aliases

The system SHALL provide short aliases for all CLI commands for use within the REPL.

#### Scenario: Aliases resolve to full commands
- **WHEN** user types `n note "Title"` at the prompt
- **THEN** the system SHALL dispatch the same logic as `new note "Title"`
- **WHEN** user types `s abc123` at the prompt
- **THEN** the system SHALL dispatch the same logic as `show abc123`

#### Scenario: Alias table defined
- **THEN** the following aliases SHALL be defined:
  - `n` → `new`
  - `s` → `show`
  - `q` → `query`
  - `l` → `link`
  - `bl` → `backlinks`
  - `g` → `graph`
  - `st` → `status`
  - `e` → `edit`
  - `af` → `add-file`
  - `v` → `verify`

#### Scenario: Full command names also work
- **WHEN** user types `new note "Title"` at the prompt
- **THEN** the system SHALL dispatch the same logic as if using an alias

### Requirement: Tab completion

The system SHALL provide tab completion within the REPL using readline.

#### Scenario: Complete commands and aliases
- **WHEN** user presses Tab at the start of an empty or partial input
- **THEN** the system SHALL complete or suggest matching commands and aliases

#### Scenario: Complete UUIDs
- **WHEN** user presses Tab after a command that expects a UUID argument
- **THEN** the system SHALL complete or suggest matching node UUIDs from the vault

#### Scenario: Complete type names
- **WHEN** user presses Tab after `new` (or alias `n`) before the type argument
- **THEN** the system SHALL complete or suggest matching type names

#### Scenario: Complete tags
- **WHEN** user presses Tab after a `--tag` or `-t` flag
- **THEN** the system SHALL complete or suggest matching tags from the vault

### Requirement: Session state

The system SHALL maintain session state across commands within a REPL session.

#### Scenario: Last UUID stored
- **WHEN** a command creates or modifies a node
- **THEN** the system SHALL store the node's UUID as the session's "last UUID"

#### Scenario: Last UUID referenced with underscore
- **WHEN** user types a command using `_` as a UUID argument
- **THEN** the system SHALL replace `_` with the stored last UUID
- **WHEN** no last UUID is stored and `_` is used
- **THEN** the system SHALL display an error "No previous node"

### Requirement: Persistent command history

The system SHALL persist command history between REPL sessions.

#### Scenario: History saved on exit
- **WHEN** the REPL session exits
- **THEN** the system SHALL write the session's command history to `~/.prism_repl_history`

#### Scenario: History restored on launch
- **WHEN** the REPL launches
- **THEN** the system SHALL read and restore command history from `~/.prism_repl_history`

#### Scenario: Navigate history
- **WHEN** user presses Up arrow at the prompt
- **THEN** the system SHALL display the previous command from history
- **WHEN** user presses Down arrow at the prompt
- **THEN** the system SHALL display the next command from history

#### Scenario: History command
- **WHEN** user types `history` at the prompt
- **THEN** the system SHALL display numbered list of all commands in the current session

### Requirement: Init and open from inside REPL

The system SHALL allow initializing and opening vaults from within a REPL session.

#### Scenario: Init from inside REPL
- **WHEN** user types `init /path/to/vault` at the prompt
- **THEN** the system SHALL initialize a new vault at the given path
- **THEN** the system SHALL connect the REPL to the new vault
- **THEN** the system SHALL transition to full REPL mode

#### Scenario: Open from inside REPL
- **WHEN** user types `open /path/to/vault` at the prompt
- **THEN** the system SHALL open the existing vault at the given path
- **THEN** the system SHALL connect the REPL to the vault
- **THEN** the system SHALL transition to full REPL mode

### Requirement: Unsupported commands in REPL

The system SHALL handle commands that do not make sense in a REPL context gracefully.

#### Scenario: tutor command in REPL
- **WHEN** user types `tutor` at the prompt
- **THEN** the system SHALL display a warning: "The tutor command cannot run inside the REPL. Run `prism tutor` from your shell."
- **THEN** the system SHALL remain in the REPL

### Requirement: Help command

The system SHALL provide a help command within the REPL.

#### Scenario: Help shows available commands
- **WHEN** user types `help` at the prompt
- **THEN** the system SHALL display a list of available commands and their aliases
- **WHEN** user types `help <command>` at the prompt
- **THEN** the system SHALL display the help text for that specific command

### Requirement: Tab completion for paths

The system SHALL provide per-segment tab completion for path-like tags in the REPL.

#### Scenario: Complete path segment at root level
- **WHEN** user types `path:/pho` and presses Tab
- **THEN** the system SHALL complete to `path:/photos` if `/photos` exists
- **THEN** the system SHALL show matching completions if multiple exist (e.g., `/photos` and `/phone`)

#### Scenario: Complete nested path segment
- **WHEN** user types `path:/photos/202` and presses Tab
- **THEN** the system SHALL complete the segment after the last `/` using children of the parent path node

#### Scenario: Complete after `--add-path` flag
- **WHEN** user types `prism new note "Title" --add-path /pho` and presses Tab
- **THEN** the system SHALL complete the path using the same per-segment logic

#### Scenario: No match on path prefix
- **WHEN** user types `path:/zzz` and presses Tab
- **THEN** the system SHALL NOT provide completions

