# Contributing to LoopEngine

Thank you for considering contributing to LoopEngine!

## Development Setup

```bash
git clone https://github.com/Prajna0106/LoopEngine.git
cd loopengine

# Create virtual environment and install dependencies
uv venv
uv sync --all-extras

# Install pre-commit hooks
pre-commit install
```

## Running Checks

```bash
make check       # lint + format + typecheck + test
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy
make test        # pytest with coverage
```

All checks must pass before submitting a PR.

## Code Style

- **Formatter/Linter**: Ruff (configured in `pyproject.toml`)
- **Type Checker**: mypy (strict mode for src, lenient for tests)
- **Python**: 3.12+ (uses `from __future__ import annotations`)
- **Line Length**: 99 characters max

### Conventions

- One interface per file in `core/ports/` (Interface Segregation Principle)
- Domain exceptions inherit from `LoopEngineError`
- All modules must have docstrings
- No circular imports: `core` must not import from `adapters` or `infrastructure`
- Use `TYPE_CHECKING` blocks for type-only imports

## Project Structure

```
src/loopengine/
  core/             # Domain layer (no external deps)
    ports/          # Abstract interfaces
    services/       # Business logic
    domain/         # Entities and exceptions
  adapters/         # Concrete implementations
    inbound/        # CLI, webhooks
    outbound/       # Agents, persistence, plugins
  infrastructure/   # Cross-cutting concerns
    config/         # Configuration
    container/      # Dependency injection
    logging/        # Structured logging
    telemetry/      # Metrics
```

## Testing

- Tests live in `tests/` mirroring the src structure
- Use fixtures in `tests/conftest.py` for shared setup
- Use factories in `tests/factories/` for domain objects
- Use stubs in `tests/stubs/` for port implementations
- Target 90%+ coverage

### Running Tests

```bash
uv run pytest                        # all tests
uv run pytest tests/unit             # unit tests only
uv run pytest tests/integration      # integration tests only
uv run pytest -k "test_name"         # specific test
```

## Submitting Changes

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run `make check` to ensure everything passes
4. Submit a pull request with a clear description

## Reporting Issues

Use GitHub Issues for bug reports and feature requests.
Include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
