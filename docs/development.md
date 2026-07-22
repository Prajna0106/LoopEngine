# Development Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

## Setup

```bash
git clone https://github.com/your-org/loopengine.git
cd loopengine

# Create venv and install all dependencies (including dev)
uv venv
uv sync --all-extras

# Verify installation
make doctor
```

## Project Layout

```
loopengine/
  pyproject.toml          # Project config, dependencies, tool settings
  Makefile                # Build commands
  src/loopengine/         # Source code
  tests/                  # Test suite
  docs/                   # Documentation
  examples/               # Example projects
```

## Build Commands

| Command | Description |
|---------|-------------|
| `make check` | Run all checks (lint + format + typecheck + test) |
| `make lint` | Lint with ruff |
| `make format` | Format with ruff |
| `make typecheck` | Type check with mypy |
| `make test` | Run pytest with coverage |

## Configuration

### Config Files

LoopEngine searches for configuration in this order:
1. `loop.yaml`
2. `loop.yml`
3. `loopengine.toml`

### Config Resolution

Configuration is resolved in this order (later overrides earlier):
1. Defaults
2. Config file values
3. Environment variable overrides (`LOOP_*`)

### Environment Variables

| Variable | Config Path | Type |
|----------|------------|------|
| `LOOP_MAX_ITERATIONS` | `engine.max_iterations` | `int` |
| `LOOP_DEFAULT_AGENT` | `engine.default_agent` | `str` |
| `LOOP_LOG_LEVEL` | `logging.level` | `str` |
| `LOOP_LOG_FORMAT` | `logging.format` | `str` |
| `LOOP_OUTPUT_FORMAT` | `cli.output_format` | `str` |
| `LOOP_PERSISTENCE_BACKEND` | `persistence.backend` | `str` |
| `LOOP_PERSISTENCE_DIR` | `persistence.directory` | `str` |
| `LOOP_PROJECT_PATH` | `engine.project_path` | `str` |

## Architecture Principles

- **Clean Architecture** -- dependencies point inward (core has zero external deps)
- **Interface Segregation** -- one interface per file in `core/ports/`
- **Dependency Injection** -- all dependencies injected via the DI container
- **Adapter Pattern** -- all external integrations are adapters behind port interfaces
- **SOLID** -- Single Responsibility, Open/Closed, Liskov, ISP, DIP

## Adding New Features

1. Define a port interface in `core/ports/outbound/`
2. Add domain exceptions in `core/domain/exceptions/`
3. Implement the service in `core/services/`
4. Create the adapter in `adapters/outbound/`
5. Add tests in `tests/unit/`
6. Update documentation

## Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files  # run manually
```

Hooks run ruff lint, ruff format, and mypy automatically on commit.

## IDE Setup

### VS Code

Install the Python extension and configure:
- Interpreter: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Linux/Mac)
- Formatter: Ruff
- Linter: Ruff
- Type Checker: mypy

### PyCharm

Set the Python interpreter to the virtual environment and configure
Ruff as the external linter.
