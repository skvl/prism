## ADDED Requirements

### Requirement: Path hierarchy as graph links

The system SHALL store parent-child relationships between path segments as directed links in the link graph.

#### Scenario: Path-parent link structure
- **WHEN** a child path segment is created
- **THEN** the child node's `links` SHALL contain a `path-parent` entry referencing the parent segment UUID
- **THEN** the parent node SHALL show the child in its backlinks

#### Scenario: Path-parent link not manually editable
- **WHEN** user runs `prism link <path-uuid> <parent-uuid>`
- **THEN** the system SHALL NOT create a `path-parent` link (these are managed internally by `prism path create`)

## MODIFIED Requirements

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
