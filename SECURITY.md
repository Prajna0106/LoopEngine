# Security Policy

## Supported Versions

| Version | Supported          |
|---------|-------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within LoopEngine, please send an email to the maintainers. All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Within 2 weeks for critical issues

## Security Considerations

LoopEngine orchestrates AI coding agents and executes commands. Key security considerations:

1. **Agent execution**: LoopEngine runs CLI commands via subprocess. Ensure agents are trusted and validated.
2. **Configuration**: API keys are stored in environment variables, never in config files.
3. **Plugins**: Only load plugins from trusted sources. The plugin system validates plugin metadata.
4. **Prompt injection**: Be cautious when passing user input to agent prompts.

## Best Practices

- Use environment variables for API keys (`LOOP_*` prefix)
- Enable validation before executing agent commands
- Review agent responses before applying changes
- Use `--dry-run` to preview workflows before execution
- Keep LoopEngine updated to the latest version
