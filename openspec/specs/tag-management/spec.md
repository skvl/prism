## ADDED Requirements

### Requirement: Add tag to node

The system SHALL allow adding one or more tags to an existing node.

Tags MUST match the pattern `\A[\w\-]+\Z` (alphanumeric, underscore, hyphen). Adding a tag that already exists on the node SHALL be a silent no-op. Adding a tag to any node type SHALL be allowed regardless of the type's schema fields.

#### Scenario: Add single tag to node

- **WHEN** user runs `prism tag add <uuid> work`
- **THEN** the node's `metadata.toml` SHALL contain `"work"` in its tags array

#### Scenario: Add multiple tags at once

- **WHEN** user runs `prism tag add <uuid> work personal ideas`
- **THEN** the node's tags SHALL contain `"work"`, `"personal"`, and `"ideas"`

#### Scenario: Adding an already-present tag is idempotent

- **WHEN** user runs `prism tag add <uuid> work` and the node already has tag `work`
- **THEN** the command SHALL succeed with no change and no error

#### Scenario: Invalid tag rejected

- **WHEN** user runs `prism tag add <uuid> "bad tag!"`
- **THEN** the command SHALL display an error and exit with code 1

#### Scenario: Add tag in REPL

- **WHEN** user runs `tag add <uuid> work` in the REPL
- **THEN** the same behavior SHALL apply as the CLI version

### Requirement: Remove tag from node

The system SHALL allow removing one or more tags from an existing node.

Removing a tag that does not exist on the node SHALL be a silent no-op.

#### Scenario: Remove single tag from node

- **WHEN** user runs `prism tag rm <uuid> work`
- **THEN** the node's tags SHALL no longer contain `"work"`

#### Scenario: Remove multiple tags at once

- **WHEN** user runs `prism tag rm <uuid> work personal`
- **THEN** the node's tags SHALL no longer contain `"work"` or `"personal"`

#### Scenario: Removing a non-existent tag is idempotent

- **WHEN** user runs `prism tag rm <uuid> nonexistent` and the node does not have that tag
- **THEN** the command SHALL succeed with no change and no error

#### Scenario: Remove tag in REPL

- **WHEN** user runs `tag rm <uuid> work` in the REPL
- **THEN** the same behavior SHALL apply as the CLI version

### Requirement: List all tags

The system SHALL list all unique tags across the vault.

Without `--count`, each tag SHALL appear once per line in sorted order. With `--count`, each tag SHALL be followed by the number of nodes that have that tag, in the format `tagname (N)`.

#### Scenario: List all tags

- **WHEN** user runs `prism tag list`
- **THEN** output SHALL list all unique tags across all nodes, one per line, sorted alphabetically

#### Scenario: List tags with counts

- **WHEN** user runs `prism tag list --count`
- **THEN** output SHALL show each tag followed by its node count in the format `tagname (N)`, sorted alphabetically

#### Scenario: List tags in empty vault

- **WHEN** user runs `prism tag list` in a vault with no nodes
- **THEN** the command SHALL produce no output and exit with code 0

#### Scenario: List tags in REPL

- **WHEN** user runs `tag list` or `tag list --count` in the REPL
- **THEN** the same behavior SHALL apply as the CLI version

### Requirement: Rename tag across all nodes

The system SHALL rename a tag from an old name to a new name across all nodes in the vault.

The new tag name MUST match `\A[\w\-]+\Z`. If a node has both the old and new tag, the old SHALL be removed (deduplication). Nodes that do not have the old tag SHALL be skipped.

#### Scenario: Rename tag

- **WHEN** user runs `prism tag rename work工作任务`
- **THEN** all nodes previously tagged `work` SHALL now have the tag `工作任务` instead

#### Scenario: Rename with existing target tag deduplicates

- **WHEN** user runs `prism tag rename work personal` and a node has both `work` and `personal`
- **THEN** that node SHALL have only `personal` (old `work` removed, `personal` deduplicated)

#### Scenario: Rename invalid new tag rejected

- **WHEN** user runs `prism tag rename work "invalid tag!"`
- **THEN** the command SHALL display an error, exit with code 1, and no nodes SHALL be modified

#### Scenario: Rename tag in REPL

- **WHEN** user runs `tag rename work personal` in the REPL
- **THEN** the same behavior SHALL apply as the CLI version

### Requirement: Tab completion in REPL

The REPL SHALL provide tab completion for tag-related subcommands.

#### Scenario: Complete tag names for rm

- **WHEN** user types `tag rm <uuid> ` and presses Tab
- **THEN** REPL SHALL complete with all existing tag names

#### Scenario: Complete tag names for rename

- **WHEN** user types `tag rename ` and presses Tab
- **THEN** REPL SHALL complete with all existing tag names (for the old-tag argument)

#### Scenario: Complete UUIDs for add and rm

- **WHEN** user types `tag add ` or `tag rm ` and presses Tab
- **THEN** REPL SHALL complete with UUIDs of nodes
