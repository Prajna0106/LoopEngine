# Configuration Reference

> TODO: Document all `loopengine.toml` configuration options.

## loopengine.toml

```toml
[engine]
max_iterations = 5
default_agent = "claude"

[agent.claude]
model = "claude-sonnet-4-20250514"
api_key_env = "ANTHROPIC_API_KEY"

[validation]
linters = ["ruff"]
type_checkers = ["mypy"]
test_runner = "pytest"
```

## Environment Variables

> TODO
