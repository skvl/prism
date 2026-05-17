## ADDED Requirements

### Requirement: Query builder form

The Query Builder tab SHALL provide a structured form for building queries against the vault.

#### Scenario: Type picker
- **WHEN** the Query Builder tab becomes active
- **THEN** the system SHALL display a type dropdown with all available node types
- **WHEN** user selects a type from the dropdown
- **THEN** the query SHALL filter to nodes of that type

#### Scenario: Tag selector
- **WHEN** the Query Builder tab becomes active
- **THEN** the system SHALL display a multi-select tag widget with all vault tags
- **WHEN** user selects one or more tags
- **THEN** the query SHALL filter to nodes matching the selected tags

#### Scenario: Text search input
- **WHEN** the Query Builder tab becomes active
- **THEN** the system SHALL display a text input field for full-text search
- **WHEN** user types text into the field
- **THEN** the query SHALL filter to nodes matching the text in title or body

#### Scenario: AND/OR/NOT toggles
- **WHEN** the Query Builder tab becomes active
- **THEN** the system SHALL display AND/OR/NOT toggle buttons for combining filters
- **WHEN** user changes the toggle between AND/OR
- **THEN** the query logic SHALL update accordingly

#### Scenario: Search on change
- **WHEN** user changes any filter in the form
- **THEN** the system SHALL automatically execute the query and update results

### Requirement: Query results

The system SHALL display query results below the form.

#### Scenario: Results table
- **WHEN** query results are available
- **THEN** the results SHALL be displayed in a table with columns: type, title, tags, updated date

#### Scenario: Result count
- **WHEN** query results are available
- **THEN** the system SHALL display the total result count above the table

#### Scenario: Navigate to result in browser
- **WHEN** user selects a row in the results table and presses Enter
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select that node and show its preview

### Requirement: Query history

The system SHALL maintain a query history within the session.

#### Scenario: Show recent queries
- **WHEN** the Query Builder tab becomes active
- **THEN** the system SHALL display a collapsible "Recent Queries" section
- **WHEN** user clicks a recent query
- **THEN** the form SHALL populate with that query's parameters
- **THEN** the query SHALL execute automatically
