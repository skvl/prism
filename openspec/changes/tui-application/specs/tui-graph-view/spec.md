## ADDED Requirements

### Requirement: Graph rendering

The Graph View tab SHALL render the vault's node graph as a force-directed visualization on a Textual Canvas.

#### Scenario: Initial render
- **WHEN** the Graph View tab becomes active
- **THEN** the system SHALL load all nodes and links from the vault
- **THEN** the system SHALL compute a force-directed layout
- **THEN** the system SHALL draw nodes as labeled boxes and edges as connecting lines on the Canvas

#### Scenario: Node appearance
- **WHEN** a node is rendered on the Canvas
- **THEN** the node label SHALL display the full node title without truncation
- **THEN** the user SHALL pan the view with arrow keys to see labels beyond the viewport
- **THEN** the node box SHALL be colored by node type (e.g., note=blue, contact=green, file=yellow)

#### Scenario: Edge appearance
- **WHEN** a link is rendered on the Canvas
- **THEN** the edge SHALL be drawn as a line between the two node boxes
- **THEN** the edge SHALL include an arrowhead indicating direction

### Requirement: Graph interaction

The system SHALL support interactive exploration of the graph.

#### Scenario: Select a node
- **WHEN** user clicks on a node in the Canvas
- **THEN** the node SHALL be highlighted with a border
- **THEN** connected nodes and edges SHALL be emphasized (others dimmed)

#### Scenario: Navigate to node in browser
- **WHEN** user presses `Enter` on a selected node
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select that node and show its preview

#### Scenario: Pan the view
- **WHEN** user presses the arrow keys
- **THEN** the Canvas viewport SHALL pan in the corresponding direction

#### Scenario: Zoom the view
- **WHEN** user presses `+` or `-`
- **THEN** the Canvas SHALL zoom in or out

### Requirement: Dense graph fallback

The system SHALL fall back to a flat list view when the graph exceeds a density threshold.

#### Scenario: Automatic fallback to list
- **WHEN** the graph has more than 50 visible nodes
- **THEN** the system SHALL display a flat list of nodes instead of the Canvas
- **THEN** each list item SHALL show the node's title, type, and connected node count

#### Scenario: Filter graph by type
- **WHEN** user presses `t` in the Graph View tab
- **THEN** the system SHALL display a type filter
- **WHEN** user selects a type
- **THEN** the graph SHALL show only nodes of that type (and their direct connections)

### Requirement: Node detail on hover

The system SHALL show node details on hover.

#### Scenario: Tooltip on hover
- **WHEN** user hovers the cursor over a node on the Canvas
- **THEN** the system SHALL display a tooltip with the node's full title, type, and tag list
