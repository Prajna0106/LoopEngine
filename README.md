# LoopEngine

[![CI](https://github.com/Prajna0106/LoopEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/Prajna0106/LoopEngine/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/loopengine.svg)](https://pypi.org/project/loopengine/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![codecov](https://codecov.io/gh/Prajna0106/LoopEngine/branch/main/graph/badge.svg)](https://codecov.io/gh/Prajna0106/LoopEngine)

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

# Initialise a project
loop init

# Run a workflow
loop run

# Check environment health
loop doctor
```

## Features

- **Multi-agent orchestration** -- Claude, Codex, OpenCode, or custom CLI agents
- **Iterative refinement** -- automatic convergence detection and re-run cycles
- **Validation pipeline** -- linting, type checking, testing, security scanning
- **Review framework** -- architecture, security, performance, documentation reviews
- **Plugin system** -- extend with custom agents, validators, and hooks
- **Prompt management** -- versioned prompt templates with variable substitution
- **Memory layer** -- persistent execution history, reflections, and project metadata
- **Structured logging** -- structlog-based with Rich/JSON rendering and tracing
- **Clean Architecture** -- fully testable, swappable adapters, SOLID principles

## Architecture

```
User / CI / Webhook
       |
       v
  +----------+    +---------------+    +---------+    +-----------+
  |  CLI /   |-->| Application   |-->| Domain  |<--| Adapters  |
  |  API     |   |  Use Cases    |   |  Core   |   | (outbound)|
  +----------+    +---------------+    +---------+    +-----------+
```

### Layer Summary

| Layer | Responsibility | Key Modules |
|-------|---------------|-------------|
| **Inbound** | CLI, webhooks, API | `adapters.inbound.cli` |
| **Ports** | Abstract interfaces (ISP) | `core.ports` |
| **Services** | Business logic | `core.services` |
| **Adapters** | Concrete implementations | `adapters.outbound` |
| **Infrastructure** | Logging, DI, config | `infrastructure` |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete design.

## CLI Commands

| Command | Description |
|---------|-------------|
| `loop init` | Initialise a LoopEngine project |
| `loop doctor` | Run environment health checks |
| `loop plan` | Plan a workflow without executing |
| `loop run` | Execute a workflow |
| `loop review <id>` | Review a completed workflow |
| `loop improve <id>` | Trigger an improvement iteration |

Global options: `--json`, `--verbose`, `--log-level`

See [docs/cli_guide.md](docs/cli_guide.md) for full CLI documentation.

## Configuration

LoopEngine supports YAML (`loop.yaml`), TOML (`loopengine.toml`), and
environment variable overrides (`LOOP_*`).

```yaml
# loop.yaml
engine:
  max_iterations: 5
  default_agent: claude

agents:
  claude:
    model: claude-sonnet-4-20250514
    api_key_env: ANTHROPIC_API_KEY

validation:
  linters: [ruff]
  type_checkers: [mypy]
  test_runner: pytest
```

See [docs/configuration_reference.md](docs/configuration_reference.md) for all options.

## Plugin Development

```python
from loopengine.core.ports.outbound.plugin_registry_port import BasePlugin, PluginMetadata

class MyPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            description="My custom plugin",
        )
```

See [docs/plugin_development.md](docs/plugin_development.md) for the full guide.

## Agent Adapters

Extend LoopEngine with any AI coding agent that has a CLI:

```python
from loopengine.adapters.outbound.agents.base_agent_adapter import BaseAgentAdapter

class MyAgentAdapter(BaseAgentAdapter):
    @property
    def name(self) -> str:
        return "my-agent"

    @property
    def command(self) -> list[str]:
        return ["my-agent-cli", "--prompt"]

    def parse_response(self, stdout: str, stderr: str) -> AgentResponse:
        return AgentResponse(content=stdout.strip())
```

See [docs/agent_integration.md](docs/agent_integration.md) for the full guide.

## Development

```bash
# Clone and set up
git clone https://github.com/Prajna0106/LoopEngine.git
cd loopengine
uv venv
uv sync --all-extras

# Run checks
make check  # lint + format + typecheck + test

# Individual commands
make lint
make format
make typecheck
make test
```

See [docs/development.md](docs/development.md) for the full development guide.
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
See [SECURITY.md](SECURITY.md) for security policy.

## Documentation

- [Architecture](ARCHITECTURE.md) -- full design document
- [CLI Guide](docs/cli_guide.md) -- command reference
- [Configuration](docs/configuration_reference.md) -- all config options
- [Plugin Development](docs/plugin_development.md) -- create custom plugins
- [Agent Integration](docs/agent_integration.md) -- integrate AI agents
- [API Reference](docs/api_reference.md) -- Python API
- [Development Guide](docs/development.md) -- setup and workflow
- [Roadmap](docs/roadmap.md) -- planned features
- [Technical Debt](docs/technical_debt.md) -- known issues and improvements
- [Changelog](CHANGELOG.md) -- version history
- [Security Policy](SECURITY.md) -- vulnerability reporting
- [Code of Conduct](CODE_OF_CONDUCT.md) -- community guidelines

## License

MIT
