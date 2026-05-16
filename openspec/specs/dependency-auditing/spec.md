## ADDED Requirements

### Requirement: Dependency vulnerability scanning with pip-audit

The system SHALL provide a way to audit third-party dependencies for known vulnerabilities using `pip-audit`.

#### Scenario: pip-audit scans dependencies from requirements files
- **WHEN** `pip-audit --strict -r requirements-prism-core.txt -r requirements-prism-cli.txt` is run
- **THEN** it SHALL report any known vulnerabilities in direct and transitive dependencies

### Requirement: Requirements files for auditing

The project SHALL maintain `requirements-prism-core.txt` and `requirements-prism-cli.txt` files that list all installable (non-local) dependencies for pip-audit to scan.

#### Scenario: Requirements file contains only PyPI-published dependencies
- **WHEN** `pip-audit` runs against the requirements files
- **THEN** it SHALL not fail due to local-only packages like `prism-core`
