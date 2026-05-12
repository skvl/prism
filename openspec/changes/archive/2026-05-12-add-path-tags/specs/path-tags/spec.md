## ADDED Requirements

### Requirement: Path type

The system SHALL define a `path` node type representing a segment in the virtual filesystem hierarchy.

#### Scenario: Path node structure
- **WHEN** a path node is created
- **THEN** its metadata SHALL have `type = "path"`
- **THEN** its metadata SHALL have `fields.name` set to the segment name
- **THEN** its metadata SHALL have no body file
- **THEN** its metadata SHALL NOT be editable via `prism edit` (path nodes are managed by `prism path` subcommands)

#### Scenario: Root path node on init
- **WHEN** `prism init` creates a new vault
- **THEN** the system SHALL create a root path node with `fields.name = "/"` and no parent link
- **THEN** the root path node UUID SHALL be stored in vault config for path resolution

### Requirement: Path creation with mkdir -p semantics

The system SHALL create path segments recursively, auto-creating parent segments as needed.

#### Scenario: Create single segment
- **WHEN** user runs `prism path create /photos`
- **THEN** the system SHALL create a path node with `fields.name = "photos"` linked to the root `/` node

#### Scenario: Create nested path
- **WHEN** user runs `prism path create /photos/2026/02/vacations`
- **THEN** the system SHALL create path nodes for `photos`, `2026`, `02`, and `vacations` if any do not exist
- **THEN** each segment SHALL link to its parent via a `path-parent` link

#### Scenario: Create existing path is no-op
- **WHEN** user runs `prism path create /photos/2026/02/vacations` and the path already exists
- **THEN** the system SHALL output the existing leaf segment UUID without creating duplicates

### Requirement: Path deletion with cascade

The system SHALL delete a path segment and its entire subtree, cleaning up node references.

#### Scenario: Delete leaf path
- **WHEN** user runs `prism path rm /photos/2026/02/vacations`
- **THEN** the system SHALL delete the `vacations` segment node
- **THEN** the system SHALL remove its UUID from all nodes' `paths` lists

#### Scenario: Delete branch path
- **WHEN** user runs `prism path rm /photos/2026`
- **THEN** the system SHALL delete `2026`, `02`, and `vacations` segment nodes
- **THEN** the system SHALL remove all their UUIDs from all nodes' `paths` lists

#### Scenario: Delete confirmation
- **WHEN** user runs `prism path rm /photos` without `--yes` and the path has children
- **THEN** the system SHALL display the number of descendant segments and nodes referencing them
- **THEN** the system SHALL prompt for confirmation before deleting

### Requirement: Associate node with path

The system SHALL allow associating nodes with paths.

#### Scenario: Add path to node on create
- **WHEN** user runs `prism new note "Beach" --add-path /photos/2026/02/vacations`
- **THEN** the system SHALL resolve the path to its leaf segment UUID
- **THEN** the system SHALL store the leaf UUID in the node's `paths` field

#### Scenario: Add path to existing node
- **WHEN** user runs `prism edit <uuid> --add-path /photos/2026/02/vacations`
- **THEN** the system SHALL add the leaf segment UUID to the node's `paths` field

#### Scenario: Remove path from node
- **WHEN** user runs `prism edit <uuid> --remove-path /photos/2026/02/vacations`
- **THEN** the system SHALL remove the leaf segment UUID from the node's `paths` field
- **THEN** the path segment node itself SHALL NOT be deleted

#### Scenario: Multiple paths per node
- **WHEN** a node is associated with both `/photos/2026/02/vacations` and `/favorites/landscapes`
- **THEN** the node's `paths` field SHALL contain both leaf segment UUIDs
- **THEN** querying either path SHALL return the node

### Requirement: Tree browsing

The system SHALL provide a tree view of the virtual filesystem hierarchy.

#### Scenario: Tree from root
- **WHEN** user runs `prism path tree`
- **THEN** the system SHALL display the full hierarchy starting from root `/`
- **THEN** each leaf node SHALL show the count of nodes filed under that path

#### Scenario: Tree from subpath
- **WHEN** user runs `prism path tree /photos/2026`
- **THEN** the system SHALL display the hierarchy starting from the given path

#### Scenario: Empty path directory
- **WHEN** user runs `prism path tree /empty`
- **THEN** the system SHALL display "No path found at /empty"

### Requirement: Path segment validation

Path segments SHALL follow character rules.

#### Scenario: Valid path segment characters
- **WHEN** creating a path with segment `vacation photos 2026`
- **THEN** the segment SHALL be accepted (spaces allowed)

#### Scenario: Invalid path segment characters
- **WHEN** creating a path with a segment containing `/`
- **THEN** the system SHALL reject with: "Invalid path segment character"

### Requirement: Path nodes as regular nodes

Path nodes SHALL support the same features as regular nodes (tagging, linking, querying).

#### Scenario: Tag a path node
- **WHEN** a path node `/photos` has `tags = ["important"]`
- **THEN** querying `tag:important` SHALL return the path node

#### Scenario: Link from path node to regular node
- **WHEN** a path node has a `[[uuid]]` link to a regular node
- **THEN** the link SHALL appear in graph exports (when paths are included)
- **THEN** the target node SHALL show a backlink from the path node
