# Agent Integration Guide

LoopEngine supports AI coding agents via CLI process invocation. Each agent
is represented by an adapter that implements the `BaseAgent` port interface.

## Built-in Agents

| Agent | CLI | Adapter |
|-------|-----|---------|
| Claude | `claude` | `ClaudeAdapter` |
| Codex | `codex` | `CodexAdapter` |
| OpenCode | `opencode` | `OpenCodeAdapter` |
| Generic CLI | any | `GenericCLIAdapter` |

## How Agents Work

Agents are invoked as subprocesses:

1. The adapter builds CLI arguments from the prompt + context
2. A subprocess is spawned with the configured timeout
3. stdout is captured and parsed into an `AgentResponse`
4. Retry logic handles transient failures

## Creating a Custom Agent Adapter

### 1. Extend `BaseAgentAdapter`

```python
from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)
from loopengine.core.ports.outbound.agent_port import AgentResponse

class MyAgentAdapter(BaseAgentAdapter):
    """Adapter for my AI coding agent."""

    def __init__(self, **kwargs):
        super().__init__(config=ProcessConfig(timeout=60.0, max_retries=2))

    @property
    def name(self) -> str:
        return "my-agent"

    @property
    def command(self) -> list[str]:
        """The base CLI command."""
        return ["my-agent-cli", "--prompt"]

    def build_args(self, prompt: str, *, context=None) -> list[str]:
        """Build full argument list."""
        args = [*self.command]
        if context and context.get("model"):
            args.extend(["--model", context["model"]])
        args.append(prompt)
        return args

    def parse_response(self, stdout: str, stderr: str) -> AgentResponse:
        """Parse CLI output into structured response."""
        return AgentResponse(
            content=stdout.strip(),
            metadata={"model": "my-agent-v1"},
        )
```

### 2. Required Overrides

| Method/Property | Description |
|----------------|-------------|
| `name` | Unique agent identifier |
| `command` | Base CLI command as list of strings |
| `parse_response(stdout, stderr)` | Parse subprocess output |

### 3. Optional Overrides

| Method | Description | Default |
|--------|-------------|---------|
| `build_args(prompt, context)` | Build full CLI args | `command + [prompt]` |
| `is_available()` | Check if CLI is installed | `shutil.which(command[0])` |
| `format_timeout_message(timeout)` | Custom timeout message | Standard message |

## Process Configuration

`ProcessConfig` controls subprocess behavior:

```python
@dataclass(frozen=True)
class ProcessConfig:
    timeout: float = 120.0      # seconds
    max_retries: int = 3        # retry count
    retry_delay: float = 1.0    # initial delay
    retry_backoff: float = 2.0  # exponential backoff
    cwd: str | None = None      # working directory
    env: dict[str, str] = {}    # extra env vars
```

## Error Handling

| Exception | When |
|-----------|------|
| `AgentTimeoutError` | Agent didn't respond within timeout (never retried) |
| `AgentRefusedError` | CLI not found or non-zero exit (not retried) |
| `AgentError` | General execution failure (retried up to max_retries) |

## Streaming

For long-running agents, use `invoke_streaming()`:

```python
proc = agent.invoke_streaming("Build the auth module")
for line in proc.stdout:
    print(line, end="")
proc.wait()
```

## Availability Check

```python
if agent.is_available():
    response = agent.invoke("Do something")
else:
    print(f"{agent.name} CLI not found on PATH")
```
