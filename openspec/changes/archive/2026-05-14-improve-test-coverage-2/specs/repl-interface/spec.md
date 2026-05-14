## MODIFIED Requirements

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
