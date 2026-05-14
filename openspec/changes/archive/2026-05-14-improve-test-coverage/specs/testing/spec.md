# Testing

## ADDED Requirements

### Requirement: Path resolution resolves root and nested paths
The PathResolver SHALL resolve absolute path strings to UUIDs by traversing the path tree via `path-parent` links.

#### Scenario: Resolve root path
- **WHEN** `PathResolver.resolve("/")` is called on a vault with a configured path root
- **THEN** it SHALL return the root node's UUID

#### Scenario: Resolve single-segment path
- **WHEN** `PathResolver.resolve("/foo")` is called and a child node with name "foo" exists under root
- **THEN** it SHALL return that child node's UUID

#### Scenario: Resolve multi-segment path
- **WHEN** `PathResolver.resolve("/foo/bar/baz")` is called and the tree has nodes foo→bar→baz linked by `path-parent`
- **THEN** it SHALL return the baz node's UUID

#### Scenario: Resolve nonexistent path raises error
- **WHEN** `PathResolver.resolve("/nonexistent")` is called
- **THEN** it SHALL raise `ValueError`

#### Scenario: Resolve without leading slash raises error
- **WHEN** `PathResolver.resolve("foo")` is called without a leading `/`
- **THEN** it SHALL raise `ValueError`

### Requirement: Path resolution creates missing segments on demand
The `resolve_or_create` method SHALL create intermediate path nodes when they don't exist.

#### Scenario: Create missing path segments
- **WHEN** `PathResolver.resolve_or_create("/new/path")` is called on a vault with only root
- **THEN** it SHALL create nodes "new" and "path" linked by `path-parent` and return the leaf UUID

#### Scenario: Create with existing prefix
- **WHEN** `PathResolver.resolve_or_create("/foo/bar")` is called and "foo" already exists
- **THEN** it SHALL create only "bar" under the existing "foo" node

#### Scenario: Invalid segment characters raise error
- **WHEN** `PathResolver.resolve_or_create("/bad spaces/invalid!chars")` is called
- **THEN** it SHALL raise `ValueError`

### Requirement: Path resolution collects descendant UUIDs
The `collect_descendants` method SHALL return all UUIDs in the subtree below a given node.

#### Scenario: Collect descendants
- **WHEN** `collect_descendants(root_uuid)` is called on a tree with root→a→b and root→c
- **THEN** it SHALL return a list containing the UUIDs of a, b, and c

#### Scenario: Cycle detection prevents cycles
- **WHEN** attaching a node whose descendant would be the target parent
- **THEN** `_would_create_cycle` SHALL return `True`

### Requirement: Path completion suggests partial paths
The `complete` method SHALL return matching path completions for a prefix.

#### Scenario: Complete partial segment
- **WHEN** `complete("/fo")` is called and a node named "foo" exists under root
- **THEN** it SHALL return `["/foo"]`

#### Scenario: Complete with multiple matches
- **WHEN** `complete("/f")` is called and nodes "foo" and "bar" exist under root
- **THEN** it SHALL return `["/bar", "/foo"]` (sorted)

#### Scenario: Complete with no matches returns empty
- **WHEN** `complete("/z")` is called and no node starts with "z" under root
- **THEN** it SHALL return `[]`

### Requirement: UUID-to-path reverse resolution works
The `resolve_uuid_to_path` method SHALL return the absolute path string for a given node UUID by walking parent links to root.

#### Scenario: Resolve UUID to path
- **WHEN** `resolve_uuid_to_path(leaf_uuid)` is called on a tree root→foo→bar→baz
- **THEN** it SHALL return `"/foo/bar/baz"`

#### Scenario: Resolve root UUID returns "/"
- **WHEN** `resolve_uuid_to_path(root_uuid)` is called
- **THEN** it SHALL return `"/"`

#### Scenario: Unknown UUID returns empty string
- **WHEN** `resolve_uuid_to_path(nonexistent_uuid)` is called
- **THEN** it SHALL return `""`

### Requirement: Node manager delete handles non-interactive paths
The `delete_node` method SHALL handle force-delete and nonexistent UIDs correctly.

#### Scenario: Force delete ignores backlinks
- **WHEN** `delete_node(uid, force=True)` is called on a node with backlinks
- **THEN** it SHALL delete the node without prompting

#### Scenario: Delete nonexistent node returns False
- **WHEN** `delete_node(nonexistent_uid)` is called
- **THEN** it SHALL return `False`

### Requirement: Show node displays path assignments
The `show_node` method SHALL include path information when a node has paths assigned.

#### Scenario: Show node with path
- **WHEN** `show_node(uid)` is called on a node with an assigned path
- **THEN** the output SHALL contain the resolved path string

### Requirement: Query engine handles NOT and edge cases
The query engine SHALL correctly evaluate `NOT` negation and handle invalid field comparisons gracefully.

#### Scenario: NOT negation excludes matching nodes
- **WHEN** executing `NOT tag:foo` against nodes tagged with and without "foo"
- **THEN** only nodes without "foo" SHALL be returned

#### Scenario: Invalid field comparison returns empty
- **WHEN** executing a query comparing a nonexistent field
- **THEN** the result SHALL be empty (no match)

#### Scenario: Nested NOT with AND works
- **WHEN** executing `tag:foo AND NOT tag:bar`
- **THEN** nodes tagged "foo" but not "bar" SHALL be returned
