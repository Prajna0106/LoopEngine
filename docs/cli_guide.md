# CLI Guide

LoopEngine provides a CLI tool (`loop`) for managing engineering workflows.
All commands delegate to service interfaces via dependency injection -- the
CLI layer contains no business logic.

## Global Options

```
loop [OPTIONS] COMMAND [ARGS]
```

| Option | Short | Description |
|--------|-------|-------------|
| `--json` | `-j` | Output results as JSON |
| `--verbose` | `-v` | Enable debug logging |
| `--log-level` | `-l` | Set log level (DEBUG, INFO, WARNING, ERROR) |

## Commands

### `loop init`

Initialise a LoopEngine project in the current directory.

```
loop init [PATH]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `PATH` | `.` | Project directory |

Creates the default configuration file and project structure.

### `loop doctor`

Run environment health checks to verify dependencies are installed.

```
loop doctor
```

Checks for:
- Python version
- Required CLI tools (git, etc.)
- Agent CLI availability
- Configuration file validity

### `loop plan`

Create an execution plan without running it.

```
loop plan [--config CONFIG]
```

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to config file (auto-detected if omitted) |

### `loop run`

Execute a workflow.

```
loop run [--config CONFIG] [--dry-run]
```

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to config file |
| `--dry-run` | Plan only, don't execute |

### `loop review`

Review a completed workflow.

```
loop review WORKFLOW_ID
```

| Argument | Description |
|----------|-------------|
| `WORKFLOW_ID` | The workflow identifier |

### `loop improve`

Trigger an improvement iteration on a workflow.

```
loop improve WORKFLOW_ID
```

| Argument | Description |
|----------|-------------|
| `WORKFLOW_ID` | The workflow identifier |

## JSON Mode

All commands support `--json` for machine-readable output:

```bash
loop --json plan
```

JSON output follows a consistent schema with `status`, `data`, and `error` fields.

## Error Handling

Errors are displayed with structured codes:

- `CONFIG_LOAD_ERROR` -- configuration file couldn't be loaded
- `CONFIG_VALIDATION_ERROR` -- configuration failed validation
- `WORKFLOW_NOT_FOUND` -- workflow ID doesn't exist
- `AGENT_TIMEOUT` -- agent didn't respond in time
- `AGENT_REFUSED` -- agent CLI returned non-zero exit code

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LOOP_LOG_LEVEL` | Override log level |
| `LOOP_LOG_FORMAT` | `console` or `json` |
| `LOOP_OUTPUT_FORMAT` | CLI output format |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 130 | Interrupted (Ctrl+C) |
