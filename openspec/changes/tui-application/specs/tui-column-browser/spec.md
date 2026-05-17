## ADDED Requirements

### Requirement: Three-column layout

The Column Browser tab SHALL display three columns: Path tree (left), Node list (middle), Preview (right).

#### Scenario: Initial state
- **WHEN** the Column Browser tab becomes active
- **THEN** the left column SHALL display the vault's path hierarchy as a tree
- **THEN** the middle column SHALL display nodes at the selected path (or root if no path selected)
- **THEN** the right column SHALL display a preview of the selected node (or empty if none selected)

#### Scenario: Column widths
- **WHEN** the TUI window is resized
- **THEN** the Path column SHALL occupy ~20% of width
- **THEN** the Nodes column SHALL occupy ~30% of width
- **THEN** the Preview column SHALL occupy ~50% of width

### Requirement: Path column

The left column SHALL display the vault's path hierarchy as an expandable/collapsible tree.

#### Scenario: Expand a path
- **WHEN** user presses `l` or `Enter` on a collapsed path node
- **THEN** the system SHALL expand the path node to show its children
- **THEN** the Nodes column SHALL update to show nodes at the selected path

#### Scenario: Collapse a path
- **WHEN** user presses `h` or `Left` on an expanded path node
- **THEN** the system SHALL collapse the path node

#### Scenario: Ascend to parent
- **WHEN** user presses `h` on the first child of a path
- **THEN** the system SHALL move focus to the parent path node

### Requirement: Node list column

The middle column SHALL display nodes at the currently selected path, showing type icon, title, and tags.

#### Scenario: Select a node
- **WHEN** user presses `j` or `Down` in the Nodes column
- **THEN** the system SHALL move selection to the next node
- **WHEN** user presses `k` or `Up` in the Nodes column
- **THEN** the system SHALL move selection to the previous node

#### Scenario: Preview updates on selection
- **WHEN** user selects a node in the Nodes column
- **THEN** the Preview column SHALL update to show the selected node's content

#### Scenario: Open node for editing
- **WHEN** user presses `e` on a selected node
- **THEN** the system SHALL launch the system `$EDITOR` with the node's body file
- **THEN** the system SHALL detect changes on editor exit and update the vault

#### Scenario: Tag filter overlay
- **WHEN** user presses `t` in the Nodes column
- **THEN** the system SHALL display a tag filter input overlay
- **WHEN** user types a tag name in the filter
- **THEN** the Nodes column SHALL narrow to show only matching nodes

#### Scenario: Type filter overlay
- **WHEN** user presses `T` in the Nodes column
- **THEN** the system SHALL display a type filter input overlay
- **WHEN** user selects a type
- **THEN** the Nodes column SHALL narrow to show only nodes of that type

### Requirement: Preview column

The right column SHALL display the selected node's content and metadata.

#### Scenario: Show node content
- **WHEN** a node with a markdown body is selected
- **THEN** the Preview column SHALL render the markdown body
- **THEN** the Preview column SHALL render `[[uuid]]` links as highlighted, clickable references

#### Scenario: Show node metadata
- **WHEN** a node is selected
- **THEN** the Preview column SHALL display the node's type, tags, creation date, and update date below the body

#### Scenario: Show backlinks count
- **WHEN** a node is selected
- **THEN** the Preview column SHALL display the count of backlinks
- **WHEN** user clicks the backlinks count
- **THEN** the system SHALL list the backlinking nodes in the preview

#### Scenario: Show fields for structured types
- **WHEN** a node with structured fields (e.g., contact, bookmark) is selected
- **THEN** the Preview column SHALL display the field values in a formatted list

### Requirement: Modal navigation

The Column Browser SHALL support ranger-style modal navigation.

#### Scenario: Navigate between columns
- **WHEN** user presses `h` or `Left` in the middle or right column
- **THEN** focus SHALL move to the previous column
- **WHEN** user presses `l` or `Right` in the left or middle column
- **THEN** focus SHALL move to the next column

#### Scenario: Quick movement
- **WHEN** user presses `gg` in any column
- **THEN** the selection SHALL jump to the first item
- **WHEN** user presses `G` in any column
- **THEN** the selection SHALL jump to the last item

#### Scenario: Refresh view
- **WHEN** user presses `r` in the Browser tab
- **THEN** the system SHALL reload the path tree, node list, and preview from the vault
