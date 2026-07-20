# LoopEngine

Engineering orchestration framework for AI coding agents.

LoopEngine is **not** an AI coding agent. It is a production-grade orchestration
framework that sits on top of AI coding agents and manages engineering workflows:
planning, execution, validation, reflection, testing, documentation, and
iterative improvement.

## Quick Start

```bash
# Install
pip install loopengine

# Or with uv
uv pip install loopengine

# Run a workflow
loopengine run --config loopengine.toml
```

## Features

- **Multi-agent orchestration** — Claude, OpenAI, Copilot, Gemini, or custom
- **Iterative refinement** — automatic convergence detection and re-run cycles
- **Validation pipeline** — linting, type checking, testing, security scanning
- **Plugin system** — extend with custom agents, validators, and hooks
- **Clean Architecture** — fully testable, swappable adapters, SOLID principles

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design.

```
User / CI / Webhook
       │
       ▼
  ┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌───────────┐
  │  CLI /  │───▶│ Application │───▶│ Domain  │◀───│ Adapters  │
  │  API    │    │  Use Cases  │    │  Core   │    │ (outbound)│
  └─────────┘    └─────────────┘    └─────────┘    └───────────┘
```

## Development

```bash
# Clone and set up
git clone https://github.com/your-org/loopengine.git
cd loopengine
uv venv
uv pip install -e ".[dev]"

# Run checks
make lint
make test
make check  # lint + typecheck + test

# Pre-commit hooks
pre-commit install
```

## License

MIT
