# Roadmap

## Completed

- [x] Clean Architecture foundation
- [x] CLI framework (Typer + Rich)
- [x] 10 abstract port interfaces (ISP-compliant)
- [x] Dependency injection container
- [x] Agent adapter framework (Claude, Codex, OpenCode, Generic CLI)
- [x] Project analyzer (language, framework, CI, Docker detection)
- [x] Planner service (intent detection, scope estimation, phase decomposition)
- [x] Execution engine (sequential execution, dependency tracking)
- [x] Reflection engine (error categorization, suggestion generation)
- [x] Validator framework (Python, pytest, Docker, Maven, npm, Gradle)
- [x] Review framework (architecture, security, performance, testing, etc.)
- [x] Plugin system (lifecycle hooks, dependency resolution, filesystem discovery)
- [x] Prompt management (versioning, variable substitution, caching)
- [x] Memory layer (execution history, reflections, reviews, project metadata)
- [x] Structured logging (structlog, Rich/JSON rendering, tracing)
- [x] Metrics collection (counters, gauges, histograms, timing)
- [x] Configuration (YAML, TOML, env vars, Pydantic validation)
- [x] 620+ tests, 91%+ coverage

## In Progress

- [ ] First end-to-end workflow (Prompt 20)
- [ ] Plugin system integration with CLI
- [ ] Prompt template library (built-in prompts)
- [ ] Documentation generation from code

## Planned

### v0.2.0 -- Core Workflow

- [ ] Interactive workflow mode
- [ ] Parallel task execution
- [ ] Workflow persistence and resume
- [ ] Agent response parsing (structured output)
- [ ] Convergence detection strategies

### v0.3.0 -- Intelligence

- [ ] ML-based scope estimation
- [ ] Historical metric analysis
- [ ] Automatic test generation
- [ ] Code diff analysis
- [ ] Performance regression detection

### v0.4.0 -- Integration

- [ ] GitHub Actions integration
- [ ] GitLab CI integration
- [ ] Webhook triggers
- [ ] Slack/Teams notifications
- [ ] Jira/Linear integration

### v0.5.0 -- Scale

- [ ] Multi-project orchestration
- [ ] Team-level workflows
- [ ] Cost tracking and budgets
- [ ] Audit logging
- [ ] Role-based access control

### v1.0.0 -- Production

- [ ] Stability guarantee
- [ ] Migration guides
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Enterprise features

## Design Principles

These principles guide all development decisions:

1. **Clean Architecture** -- core has zero external dependencies
2. **Interface Segregation** -- one interface per file, minimal methods
3. **Adapter Pattern** -- all external integrations are swappable
4. **Testability** -- every module is independently testable
5. **CLI-first** -- the CLI is the primary interface
6. **Convention over Configuration** -- sensible defaults, explicit overrides
