# Custom Agent Adapter Example

This example shows how to create a custom agent adapter for LoopEngine.

## Create the Adapter

```python
# my_agent_adapter.py
from loopengine.adapters.outbound.agents.base_agent_adapter import (
    BaseAgentAdapter,
    ProcessConfig,
)
from loopengine.core.ports.outbound.agent_port import AgentResponse

class MyAgentAdapter(BaseAgentAdapter):
    """Adapter for a custom AI coding agent."""

    def __init__(self, **kwargs):
        super().__init__(
            config=ProcessConfig(timeout=90.0, max_retries=2),
            **kwargs,
        )

    @property
    def name(self) -> str:
        return "my-agent"

    @property
    def command(self) -> list[str]:
        return ["my-agent-cli", "--prompt"]

    def build_args(self, prompt: str, *, context=None) -> list[str]:
        args = [*self.command]
        if context:
            if context.get("model"):
                args.extend(["--model", context["model"]])
            if context.get("temperature"):
                args.extend(["--temp", str(context["temperature"])])
        args.append(prompt)
        return args

    def parse_response(self, stdout: str, stderr: str) -> AgentResponse:
        return AgentResponse(
            content=stdout.strip(),
            metadata={"agent": "my-agent"},
        )
```

## Use the Adapter

```python
agent = MyAgentAdapter()
if agent.is_available():
    response = agent.invoke("Build the authentication module")
    print(response.content)
```

## See Also

- [Agent Integration Guide](../../docs/agent_integration.md)
- [API Reference](../../docs/api_reference.md)
