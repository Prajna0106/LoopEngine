# Basic Workflow Example

This example demonstrates a basic LoopEngine workflow.

## Setup

```bash
cd examples/basic_workflow
loop init
```

## Configuration

Create a `loop.yaml`:

```yaml
engine:
  max_iterations: 3
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

## Run

```bash
# Plan only
loop plan

# Execute
loop run

# Review results
loop review <workflow-id>
```

## What Happens

1. Planner creates an execution plan from the goal
2. Execution engine runs each task via the configured agent
3. Validators check linting, types, and tests
4. Reviewers assess architecture, security, and performance
5. Reflection engine determines if convergence was reached
6. If not, the loop iterates with fixes applied
