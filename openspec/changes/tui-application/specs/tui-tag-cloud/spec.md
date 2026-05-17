## ADDED Requirements

### Requirement: Tag cloud display

The Tag Cloud tab SHALL display all tags in the vault as a weighted visual layout.

#### Scenario: Initial tag cloud
- **WHEN** the Tag Cloud tab becomes active
- **THEN** the system SHALL load all tags with their node counts from the vault
- **THEN** the system SHALL display tags sized proportionally to their frequency (more nodes = larger text)

#### Scenario: Tag appearance
- **WHEN** a tag is displayed in the cloud
- **THEN** the tag text SHALL show the tag name and count (e.g., "work (12)")
- **THEN** tags with higher counts SHALL appear in a more prominent style (larger, brighter)

### Requirement: Tag cloud interaction

The system SHALL support interactive tag exploration.

#### Scenario: Select tag to filter
- **WHEN** user clicks a tag in the cloud
- **THEN** the tag SHALL be highlighted as selected
- **THEN** the system SHALL display a list of nodes with that tag below the cloud

#### Scenario: Multiple tag selection (AND)
- **WHEN** user clicks a second tag while a first is selected
- **THEN** the system SHALL add the tag to the selection
- **THEN** the node list SHALL narrow to nodes matching ALL selected tags

#### Scenario: Navigate to node in browser
- **WHEN** user clicks a node in the filtered result list
- **THEN** the system SHALL switch to the Column Browser tab
- **THEN** the system SHALL select that node and show its preview

#### Scenario: Clear tag filter
- **WHEN** user presses `Esc` or clicks the "Clear" button
- **THEN** the system SHALL clear all tag selections
- **THEN** the node list SHALL show all nodes again

### Requirement: Co-occurrence hint

The system SHALL visually hint tag co-occurrence.

#### Scenario: Related tags highlighted
- **WHEN** user selects a tag
- **THEN** tags that frequently co-occur with the selected tag SHALL appear with a subtle highlight or border
