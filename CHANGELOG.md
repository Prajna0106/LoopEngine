# Changelog

All notable changes to LoopEngine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project scaffold with Clean Architecture
- CLI layer with Typer and Rich
- Configuration system (YAML, TOML, env vars)
- 10 abstract port interfaces (ISP-compliant)
- Dependency injection container
- Agent adapter framework (Claude, Codex, OpenCode, Generic)
- Project analyzer with language/framework detection
- Planner with intent detection and phase decomposition
- Execution engine with dependency tracking
- Reflection engine with error categorization
- Validator framework (Python, Pytest, Maven, Gradle, NPM, Docker)
- Review framework (Architecture, Security, Performance, Documentation, Testing, Complexity, Scalability, API Design, Database)
- Plugin system with discovery and lifecycle management
- Prompt management with versioning and caching
- Memory layer with SQLite and in-memory stores
- Structured logging with structlog and tracing
- Metrics collection with timing support
- Testing infrastructure with 633 tests at 90%+ coverage
- Documentation: CLI guide, plugin development, agent integration, API reference, roadmap
- Technical debt report

### Changed
- Consolidated agent adapter defaults into `BaseAgentAdapter`
- Shared subprocess utilities extracted to `_subprocess_utils.py`
- Config exceptions moved to `core/domain/exceptions/`

## [0.1.0] - 2026-07-22

### Added
- Initial alpha release
- Core architecture and interfaces
- CLI commands: init, doctor, plan, run, review, improve
- Multi-agent support
- Validation and review pipelines
- Plugin and prompt management
