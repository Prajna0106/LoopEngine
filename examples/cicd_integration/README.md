# CI/CD Integration Example

This example shows how to integrate LoopEngine into CI/CD pipelines.

## GitHub Actions

```yaml
# .github/workflows/loopengine.yml
name: LoopEngine

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  orchestrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --all-extras
      - run: uv run loop run --config loop.yaml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - orchestrate

loopengine:
  stage: orchestrate
  image: python:3.12
  script:
    - pip install uv
    - uv sync --all-extras
    - uv run loop run
  variables:
    ANTHROPIC_API_KEY: $ANTHROPIC_API_KEY
```

## Local Pre-commit

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: loopengine
        name: LoopEngine
        entry: uv run loop run --dry-run
        language: system
        pass_filenames: false
```

## Environment Variables

Set these in your CI environment:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `LOOP_LOG_LEVEL` | Log level (default: INFO) |
| `LOOP_LOG_FORMAT` | `json` for CI |
