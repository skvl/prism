## ADDED Requirements

### Requirement: Interactive tutorial command

The system SHALL provide a `prism tutor` command that launches an interactive, terminal-based tutorial for learning Prism.

#### Scenario: Start tutorial from scratch
- **WHEN** user runs `prism tutor`
- **THEN** the system SHALL create a temporary vault in a sandbox directory
- **THEN** the system SHALL display the first lesson title and introduction
- **THEN** the system SHALL enter interactive mode, awaiting user input

#### Scenario: Start tutorial at specific lesson
- **WHEN** user runs `prism tutor --lesson 4`
- **THEN** the system SHALL skip lessons 1-3
- **THEN** the system SHALL display lesson 4 introduction and proceed interactively

#### Scenario: Tutorial detects no valid lesson number
- **WHEN** user runs `prism tutor --lesson 99`
- **THEN** the system SHALL display "Lesson not found. Available: 1-7."
- **THEN** the system SHALL fall back to lesson 1

### Requirement: Lesson structure

The tutorial SHALL provide 7 sequentially ordered lessons covering core Prism workflows.

#### Scenario: Lesson sequence defined
- **WHEN** the tutorial loads
- **THEN** lessons SHALL be ordered: vault basics, creating notes, multiple types, linking and graph, querying, file import, change tracking
- **THEN** each lesson SHALL contain an introduction, 3-4 interactive steps, and a summary

#### Scenario: Lesson progression
- **WHEN** user completes all steps in a lesson
- **THEN** the system SHALL display the lesson summary
- **THEN** the system SHALL proceed to the next lesson automatically

### Requirement: Interactive step execution

Each step SHALL guide the user through running a Prism command and verify the result.

#### Scenario: Display step content
- **WHEN** a step begins
- **THEN** the system SHALL display a concept explanation
- **THEN** the system SHALL display the command to run
- **THEN** the system SHALL prompt the user to type the command or press ENTER to auto-run

#### Scenario: User types correct command
- **WHEN** user types a command matching the expected command
- **THEN** the system SHALL execute the command
- **THEN** the system SHALL verify the vault state matches expectations
- **THEN** the system SHALL display the command's stdout output (if non-empty)
- **THEN** the system SHALL display a success indicator
- **THEN** the system SHALL proceed to the next step

#### Scenario: User presses ENTER to auto-run
- **WHEN** user presses ENTER without typing a command
- **THEN** the system SHALL execute the expected command automatically
- **THEN** the system SHALL verify the vault state
- **THEN** the system SHALL display the command's stdout output (if non-empty)
- **THEN** the system SHALL display a success indicator

#### Scenario: User types wrong command
- **WHEN** user types a command that differs from the expected command
- **THEN** the system SHALL display a warning with the difference
- **THEN** the system SHALL offer one retry: "Try again? [Y/n]"
- **WHEN** user chooses to retry
- **THEN** the system SHALL re-prompt for the command
- **WHEN** user chooses to skip
- **THEN** the system SHALL run the expected command automatically and proceed

#### Scenario: Command execution fails
- **WHEN** the executed command exits with a non-zero status
- **THEN** the system SHALL display the error output
- **THEN** the system SHALL offer a retry

### Requirement: State verification

The tutorial SHALL verify vault state after each step using the Prism library API.

#### Scenario: Verify after creating vault
- **WHEN** user runs `prism init <path>`
- **THEN** the system SHALL confirm the vault directory structure exists
- **THEN** the system SHALL display "Vault created!"

#### Scenario: Verify after creating node
- **WHEN** user runs `prism new note "title" --tag work`
- **THEN** the system SHALL confirm `list_nodes()` returns the new node
- **THEN** the system SHALL confirm the node type is `note`
- **THEN** the system SHALL confirm the node has tag `work`

#### Scenario: Verify after linking nodes
- **WHEN** user runs `prism link <source> <target>`
- **THEN** the system SHALL confirm the source metadata contains the link entry

#### Scenario: Verify after importing file
- **WHEN** user runs `prism add <file>`
- **THEN** the system SHALL confirm a new node exists with matching `blob_sha256`

### Requirement: Edit step without $EDITOR

The tutorial SHALL handle the edit command without launching an external editor.

#### Scenario: Tutorial demonstrates change tracking
- **WHEN** the tutorial reaches the edit lesson
- **THEN** the system SHALL write content directly to the node's `data.md` file
- **THEN** the system SHALL display "I've written an update to your note. Run `prism status` to see what happened."
- **THEN** the user runs the status command
- **THEN** the system SHALL display "The vault detected the change automatically."

### Requirement: Cleanup on exit

The tutorial SHALL manage its temporary vault lifecycle.

#### Scenario: Keep vault on completion
- **WHEN** user completes all 7 lessons
- **THEN** the system SHALL ask "Tutorial complete! Keep your practice vault? [y/N]"
- **WHEN** user answers "y"
- **THEN** the system SHALL print the vault path
- **THEN** the system SHALL exit with status 0

#### Scenario: Discard vault on completion
- **WHEN** user completes all 7 lessons
- **THEN** the system SHALL ask "Tutorial complete! Keep your practice vault? [y/N]"
- **WHEN** user answers "n" or presses ENTER
- **THEN** the system SHALL delete the temporary vault directory
- **THEN** the system SHALL exit with status 0

#### Scenario: Interrupt during tutorial
- **WHEN** user presses Ctrl+C during a lesson
- **THEN** the system SHALL catch KeyboardInterrupt
- **THEN** the system SHALL display "Tutorial paused. Run `prism tutor --lesson N` to resume."
- **THEN** the system SHALL exit with status 0

### Requirement: Lesson content

The tutorial SHALL deliver specific lessons with defined content.

#### Scenario: Lesson 1 — What's a vault?
- **WHEN** user starts lesson 1
- **THEN** the system SHALL explain: a vault is a folder that holds all notes, contacts, and files
- **THEN** step 1 SHALL run `prism init` to create a vault
- **THEN** the system SHALL explain the vault directory structure

#### Scenario: Lesson 2 — Your first note
- **WHEN** user starts lesson 2
- **THEN** the system SHALL explain: a node is a typed "thing" in your vault
- **THEN** step 1 SHALL create a note node
- **THEN** step 2 SHALL display the node with `prism show`
- **THEN** step 3 SHALL query by tag

#### Scenario: Lesson 3 — Different kinds of things
- **WHEN** user starts lesson 3
- **THEN** the system SHALL explain: types give nodes the right fields
- **THEN** steps SHALL create a contact and a bookmark
- **THEN** the system SHALL demonstrate querying by type

#### Scenario: Lesson 4 — Connecting ideas
- **WHEN** user starts lesson 4
- **THEN** the system SHALL explain: knowledge isn't isolated — nodes link to each other
- **THEN** steps SHALL create a link, show backlinks, and export the graph
- **THEN** the system SHALL highlight the graph output showing connections

#### Scenario: Lesson 5 — Finding things
- **WHEN** user starts lesson 5
- **THEN** the system SHALL explain: Prism has a powerful query language
- **THEN** steps SHALL demonstrate AND/OR/NOT queries
- **THEN** steps SHALL demonstrate full-text search

#### Scenario: Lesson 6 — Files in the vault
- **WHEN** user starts lesson 6
- **THEN** the system SHALL explain: a vault can store any file
- **THEN** steps SHALL create a temp file and import it with `prism add`
- **THEN** steps SHALL verify integrity with `prism verify`

#### Scenario: Lesson 7 — Your vault is alive
- **WHEN** user starts lesson 7
- **THEN** the system SHALL explain: Prism tracks changes to your nodes
- **THEN** the system SHALL write a change to a note body directly
- **THEN** steps SHALL run `prism status` to see the detected change
- **THEN** the system SHALL summarize what the user has learned
