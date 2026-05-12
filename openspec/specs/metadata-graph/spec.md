## Purpose

The metadata-graph capability manages directed links between nodes, backlink tracking, and graph export for visualizing the knowledge graph in DOT and JSON formats.
## Requirements
### Requirement: Create explicit link between nodes

The system SHALL support creating a directed link from one node to another.

#### Scenario: Link two nodes
- **WHEN** user runs `prism link <source-uuid> <target-uuid>`
- **THEN** the system SHALL add `{target: <target-uuid>, type: <target-type>, title: <target-title>}` to source node's metadata.toml `links` array
- **THEN** the system SHALL add the source UUID to the target node's backlinks index

#### Scenario: Link to non-existent node
- **WHEN** user runs `prism link <uuid> <non-existent-uuid>`
- **THEN** the system SHALL warn: "Target node does not exist in any registered vault"
- **THEN** the system SHALL still create the link (lazy resolution — it may resolve later when another vault is registered)

### Requirement: Parse `[[uuid]]` links from note bodies

The system SHALL detect and extract `[[uuid]]` patterns from note body markdown files.

#### Scenario: Extract links on edit
- **WHEN** user saves a note in `prism edit` containing `[[a1b2c3d4-...]]` and `[[other-vault-uuid::f1e2d3c4-...]]`
- **THEN** the system SHALL extract all UUIDs and vault-qualified UUIDs from the body
- **THEN** the system SHALL update the node's metadata.toml `links` array
- **THEN** the system SHALL rebuild the backlinks index

#### Scenario: Remove stale links
- **WHEN** user removes all `[[uuid]]` references to a previously linked node
- **THEN** the system SHALL remove that entry from the links array
- **THEN** the system SHALL remove the backlink entry

### Requirement: Backlinks

The system SHALL track which nodes link to a given node.

#### Scenario: Show backlinks
- **WHEN** user runs `prism backlinks <uuid>`
- **THEN** the system SHALL display all nodes that link to the given UUID
- **THEN** each entry SHALL show the source node's title, type, and UUID

#### Scenario: Backlinks survive node deletion
- **WHEN** a node that has backlinks is deleted
- **THEN** the backlinks SHALL remain in the index as unresolved references

### Requirement: Graph export

The system SHALL export the node graph in standard formats.

#### Scenario: Export DOT format without paths
- **WHEN** user runs `prism graph --format dot`
- **THEN** the system SHALL output a DOT graph where nodes are labeled with title + type and edges are directed links
- **THEN** the output SHALL NOT include nodes of type `path`
- **THEN** the output SHALL be suitable for rendering with Graphviz

#### Scenario: Export DOT format with paths
- **WHEN** user runs `prism graph --format dot --include-paths`
- **THEN** the system SHALL include path nodes and their `path-parent` edges in the DOT output

#### Scenario: Export JSON format without paths
- **WHEN** user runs `prism graph --format json`
- **THEN** the system SHALL output a JSON object with `nodes` array (uuid, title, type, tags) and `edges` array (source, target)
- **THEN** the output SHALL NOT include nodes of type `path`

#### Scenario: Export JSON format with paths
- **WHEN** user runs `prism graph --format json --include-paths`
- **THEN** the system SHALL include path nodes and their `path-parent` edges in the JSON output

### Requirement: Cross-vault lazy link resolution

Links to nodes in other vaults SHALL resolve lazily.

#### Scenario: Cross-vault link with vault registered
- **WHEN** vault A is registered and vault B is registered
- **THEN** a link `[[vault-B-uuid::target-uuid]]` in a note from vault A SHALL resolve to the target node's cached title and type
- **THEN** `prism show` on the source node SHALL display the resolved link

#### Scenario: Cross-vault link without vault registered
- **WHEN** vault B is NOT registered
- **THEN** the link SHALL display as "unresolved link (vault not registered)"
- **THEN** the system SHALL NOT error — the link is valid but pending

### Requirement: Path hierarchy as graph links

The system SHALL store parent-child relationships between path segments as directed links in the link graph.

#### Scenario: Path-parent link structure
- **WHEN** a child path segment is created
- **THEN** the child node's `links` SHALL contain a `path-parent` entry referencing the parent segment UUID
- **THEN** the parent node SHALL show the child in its backlinks

#### Scenario: Path-parent link not manually editable
- **WHEN** user runs `prism link <path-uuid> <parent-uuid>`
- **THEN** the system SHALL NOT create a `path-parent` link (these are managed internally by `prism path create`)

