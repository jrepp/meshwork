# Development Workflow

Meshwork uses `uv` for dependency management and `pre-commit` for local commit
gates.

## Install

```bash
uv sync --group dev
uv run --group dev pre-commit install
```

## Checks

Run the same checks used by the commit hook:

```bash
uv run --group dev pre-commit run --all-files
```

Or run the project script directly:

```bash
uv run --group dev python scripts.py check
```

The hook enforces:

- Ruff formatting
- Ruff linting
- scoped mypy checks for the new public API surface
- Python compile/conformance checks
- pytest

## Coverage

Coverage is enabled in the default pytest configuration. To also write HTML and
XML reports, run:

```bash
uv run --group dev python scripts.py coverage
```

Reports are written to `htmlcov/` and `coverage.xml`.

## Integration Tests

Integration tests use Testcontainers and require a working Docker runtime.

```bash
uv sync --group dev
uv run --group dev python scripts.py integration
```

The default pre-commit hook runs the unit suite. Container-backed tests are kept
as an explicit command so ordinary commits do not require Docker.

## Type Checking

The current checked surface is intentionally scoped to the new composable API:

```text
meshwork/core
meshwork/transports/memory.py
tests/test_public_api.py
```

See `docs/type-debt.md` for the expansion policy and legacy type-debt notes.
