## Why

Three untested or lightly tested areas create risk: the `path/resolver.py` module has zero tests (12% coverage), `node/manager.py` has untested non-interactive paths, and `query/engine.py` has uncovered edge cases. Overall coverage is 82% — filling these gaps reduces regression risk and makes refactoring safer.

## What Changes

- Write comprehensive tests for `prism/path/resolver.py` covering all 7 public methods
- Add tests for `node/manager.py` `delete_node(force=True)`, `delete_node(nonexistent)`, and `show_node` with path assignments
- Add tests for `query/engine.py` `NOT` negation and invalid field comparison edge cases

## Capabilities

### New Capabilities
- `testing`: Test coverage for path resolution, manager edge cases, and query engine edge cases. No new user-facing features — this is purely testing existing functionality.

### Modified Capabilities
<!-- No existing capabilities have their requirements changed -->

## Impact

- `prism-core/tests/` gains a new `test_path_resolver.py` file
- `prism-core/tests/test_manager.py` gains test cases
- `prism-core/tests/test_query.py` gains test cases
- No source code changes — tests only
