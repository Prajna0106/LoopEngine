# LoopEngine — Production-Grade Architecture Design

---

## 1. Folder Structure

```
loopengine/
├── pyproject.toml
├── Makefile
├── README.md
├── LICENSE
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
│
├── src/
│   └── loopengine/
│       ├── __init__.py
│       ├── __main__.py                          # CLI entrypoint
│       │
│       │─────────────────────────────────────────
│       │  DOMAIN LAYER  (innermost — zero deps)
│       │─────────────────────────────────────────
│       ├── core/
│       │   ├── __init__.py
│       │   │
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   │
│       │   │   ├── entities/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── workflow.py              # Aggregate root
│       │   │   │   ├── phase.py                 # Phase within a workflow
│       │   │   │   ├── step.py                  # Atomic unit inside a phase
│       │   │   │   ├── artifact.py              # Output of any phase/step
│       │   │   │   └── session.py               # Runtime execution session
│       │   │   │
│       │   │   ├── value_objects/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── workflow_id.py           # UUID wrapper
│       │   │   │   ├── phase_type.py            # Enum: PLAN, EXECUTE, VALIDATE, ...
│       │   │   │   ├── phase_status.py          # Enum: PENDING, RUNNING, ...
│       │   │   │   ├── workflow_status.py       # Enum: CREATED, RUNNING, ...
│       │   │   │   ├── artifact_kind.py         # Enum: CODE, TEST, DOC, ...
│       │   │   │   ├── agent_config.py          # Agent targeting config
│       │   │   │   ├── severity.py              # INFO, WARN, ERROR, CRITICAL
│       │   │   │   ├── result.py                # Result[T, E] monad
│       │   │   │   ├── prompt.py                # Immutable prompt wrapper
│       │   │   │   └── context_payload.py       # Immutable context state
│       │   │   │
│       │   │   ├── events/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base_event.py            # Abstract domain event
│       │   │   │   ├── workflow_events.py       # Created, Started, Completed, Failed
│       │   │   │   ├── phase_events.py          # Started, Completed, Failed
│       │   │   │   ├── artifact_events.py       # Created, Updated, Consumed
│       │   │   │   ├── agent_events.py          # Invoked, Responded, TimedOut
│       │   │   │   └── validation_events.py     # Passed, Failed, Warning
│       │   │   │
│       │   │   ├── exceptions/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py                  # LoopEngineException
│       │   │   │   ├── workflow_exceptions.py   # InvalidTransition, WorkflowNotFound
│       │   │   │   ├── agent_exceptions.py      # AgentTimeout, AgentRefused
│       │   │   │   └── plugin_exceptions.py     # PluginLoadError, HookNotFound
│       │   │   │
│       │   │   └── policies/
│       │   │       ├── __init__.py
│       │   │       ├── convergence_policy.py    # Abstract — when to stop iterating
│       │   │       ├── retry_policy.py          # Abstract — retry semantics
│       │   │       ├── escalation_policy.py     # Abstract — human escalation
│       │   │       └── composed_policy.py       # Combines multiple policies
│       │   │
│       │   ├── ports/                           # Interface contracts (Hexagonal)
│       │   │   ├── __init__.py
│       │   │   ├── inbound/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── orchestrator_port.py     # Start/stop/status queries
│       │   │   │   ├── workflow_command.py       # Command-port for mutations
│       │   │   │   └── workflow_query.py        # Query-port for reads
│       │   │   │
│       │   │   └── outbound/
│       │   │       ├── __init__.py
│       │   │       ├── agent_port.py            # Invoke external AI agent
│       │   │       ├── persistence_port.py      # Store/retrieve workflow state
│       │   │       ├── event_bus_port.py        # Publish domain events
│       │   │       ├── filesystem_port.py       # Read/write project files
│       │   │       ├── clock_port.py            # Time abstraction
│       │   │       ├── id_port.py               # ID generation abstraction
│       │   │       └── plugin_registry_port.py  # Register/query plugins
│       │   │
│       │   └── services/                        # Domain services (pure logic)
│       │       ├── __init__.py
│       │       ├── workflow_engine.py           # Core orchestration FSM
│       │       ├── phase_scheduler.py           # Phase ordering & transitions
│       │       ├── convergence_analyzer.py      # Determines iteration necessity
│       │       ├── context_assembler.py         # Builds agent prompts from state
│       │       └── artifact_analyzer.py         # Extracts signals from artifacts
│       │
│       │─────────────────────────────────────────
│       │  APPLICATION LAYER  (use cases)
│       │─────────────────────────────────────────
│       ├── application/
│       │   ├── __init__.py
│       │   │
│       │   ├── use_cases/
│       │   │   ├── __init__.py
│       │   │   ├── start_workflow.py            # Create & initialize workflow
│       │   │   ├── run_phase.py                 # Execute a single phase
│       │   │   ├── execute_full_cycle.py        # Run all phases end-to-end
│       │   │   ├── validate_artifact.py         # Validate a specific artifact
│       │   │   ├── reflect_and_decide.py        # Analyze & decide next action
│       │   │   ├── iterate_workflow.py          # Trigger next iteration
│       │   │   ├── get_workflow_status.py       # Read-only status query
│       │   │   └── cancel_workflow.py           # Graceful cancellation
│       │   │
│       │   ├── services/
│       │   │   ├── __init__.py
│       │   │   ├── workflow_application_service.py  # Coordinates use cases
│       │   │   ├── agent_orchestration_service.py   # Agent lifecycle mgmt
│       │   │   └── reporting_service.py             # Status & metrics
│       │   │
│       │   ├── dto/
│       │   │   ├── __init__.py
│       │   │   ├── workflow_dto.py
│       │   │   ├── phase_dto.py
│       │   │   ├── agent_request_dto.py
│       │   │   ├── agent_response_dto.py
│       │   │   ├── validation_result_dto.py
│       │   │   └── status_report_dto.py
│       │   │
│       │   └── event_handlers/
│       │       ├── __init__.py
│       │       ├── workflow_event_handler.py    # Side-effects on workflow events
│       │       ├── validation_handler.py        # Auto-trigger on validation events
│       │       └── notification_handler.py      # Notify external systems
│       │
│       │─────────────────────────────────────────
│       │  ADAPTER LAYER  (inbound + outbound)
│       │─────────────────────────────────────────
│       ├── adapters/
│       │   ├── __init__.py
│       │   │
│       │   ├── inbound/                         # Driving adapters (entry points)
│       │   │   ├── __init__.py
│       │   │   ├── cli/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── app.py                   # Click/Typer app
│       │   │   │   ├── commands/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── run.py               # `loopengine run`
│       │   │   │   │   ├── status.py            # `loopengine status`
│       │   │   │   │   ├── plugin.py            # `loopengine plugin`
│       │   │   │   │   └── init_cmd.py          # `loopengine init`
│       │   │   │   └── formatters/
│       │   │   │       ├── __init__.py
│       │   │   │       ├── console_formatter.py
│       │   │   │       └── json_formatter.py
│       │   │   │
│       │   │   ├── api/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── server.py
│       │   │   │   ├── routes/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   ├── workflow_routes.py
│       │   │   │   │   ├── health_routes.py
│       │   │   │   │   └── webhook_routes.py
│       │   │   │   ├── schemas/
│       │   │   │   │   ├── __init__.py
│       │   │   │   │   └── request_schemas.py
│       │   │   │   └── middleware/
│       │   │   │       ├── __init__.py
│       │   │   │       └── auth_middleware.py
│       │   │   │
│       │   │   └── webhook/
│       │   │       ├── __init__.py
│       │   │       └── handler.py
│       │   │
│       │   └── outbound/                        # Driven adapters (implementations)
│       │       ├── __init__.py
│       │       │
│       │       ├── agents/
│       │       │   ├── __init__.py
│       │       │   ├── base_agent_adapter.py    # ABC for all agent adapters
│       │       │   ├── claude_adapter.py
│       │       │   ├── openai_adapter.py
│       │       │   ├── copilot_adapter.py
│       │       │   ├── gemini_adapter.py
│       │       │   └── custom_adapter.py        # User-configurable adapter
│       │       │
│       │       ├── persistence/
│       │       │   ├── __init__.py
│       │       │   ├── json_file_store.py
│       │       │   ├── sqlite_store.py
│       │       │   └── in_memory_store.py       # For testing
│       │       │
│       │       ├── validation/
│       │       │   ├── __init__.py
│       │       │   ├── base_validator.py
│       │       │   ├── linter_validator.py
│       │       │   ├── type_checker_validator.py
│       │       │   ├── test_runner_validator.py
│       │       │   └── security_scanner_validator.py
│       │       │
│       │       ├── filesystem/
│       │       │   ├── __init__.py
│       │       │   └── local_filesystem.py
│       │       │
│       │       ├── events/
│       │       │   ├── __init__.py
│       │       │   ├── in_memory_event_bus.py
│       │       │   └── async_event_bus.py
│       │       │
│       │       ├── clock/
│       │       │   ├── __init__.py
│       │       │   └── system_clock.py
│       │       │
│       │       └── cicd/
│       │           ├── __init__.py
│       │           ├── github_actions_adapter.py
│       │           └── gitlab_ci_adapter.py
│       │
│       │─────────────────────────────────────────
│       │  PLUGIN SYSTEM
│       │─────────────────────────────────────────
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── plugin_base.py                   # Abstract plugin interface
│       │   ├── plugin_loader.py                 # Discovery & import
│       │   ├── plugin_registry.py               # Runtime registration
│       │   ├── hook_types.py                    # Enum of available hooks
│       │   ├── hook_dispatcher.py               # Invoke registered hooks
│       │   └── builtin/
│       │       ├── __init__.py
│       │       ├── coverage_enhancer.py         # Coverage analysis plugin
│       │       ├── security_hardener.py         # Security scanning plugin
│       │       ├── doc_generator.py             # Auto-documentation plugin
│       │       └── metrics_collector.py         # Metrics aggregation plugin
│       │
│       │─────────────────────────────────────────
│       │  INFRASTRUCTURE LAYER  (outermost)
│       │─────────────────────────────────────────
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── config/
│       │   │   ├── __init__.py
│       │   │   ├── settings.py                  # Pydantic Settings
│       │   │   ├── schema.py                    # Config model
│       │   │   └── loader.py                    # TOML/YAML file loading
│       │   ├── container/
│       │   │   ├── __init__.py
│       │   │   └── di_container.py              # wiring all adapters → ports
│       │   ├── logging/
│       │   │   ├── __init__.py
│       │   │   └── structured_logger.py
│       │   └── telemetry/
│       │       ├── __init__.py
│       │       └── metrics.py
│       │
│       │─────────────────────────────────────────
│       │  SHARED KERNEL
│       │─────────────────────────────────────────
│       └── shared/
│           ├── __init__.py
│           ├── types.py                         # Generic type aliases
│           ├── immutable.py                     # Frozen dataclass base
│           └── serialization.py                 # Safe serialization helpers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                              # Shared fixtures
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── domain/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_workflow.py
│   │   │   │   ├── test_phase.py
│   │   │   │   ├── test_step.py
│   │   │   │   ├── test_artifact.py
│   │   │   │   └── test_convergence_analyzer.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_workflow_engine.py
│   │   │   │   └── test_phase_scheduler.py
│   │   │   └── policies/
│   │   │       ├── __init__.py
│   │   │       └── test_composed_policy.py
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── use_cases/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_start_workflow.py
│   │   │   │   ├── test_run_phase.py
│   │   │   │   └── test_iterate_workflow.py
│   │   │   └── services/
│   │   │       └── test_workflow_application_service.py
│   │   │
│   │   └── plugins/
│   │       ├── __init__.py
│   │       ├── test_plugin_loader.py
│   │       └── test_hook_dispatcher.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── persistence/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_json_store.py
│   │   │   │   └── test_sqlite_store.py
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_claude_adapter.py
│   │   │   │   └── test_openai_adapter.py
│   │   │   └── events/
│   │   │       └── test_event_bus.py
│   │   ├── plugins/
│   │   │   ├── __init__.py
│   │   │   └── test_full_plugin_cycle.py
│   │   └── container/
│   │       └── test_di_wiring.py
│   │
│   ├── acceptance/
│   │   ├── __init__.py
│   │   ├── test_full_workflow_lifecycle.py
│   │   ├── test_plugin_installation.py
│   │   └── test_cli_end_to_end.py
│   │
│   └── stubs/                                  # Test doubles
│       ├── __init__.py
│       ├── stub_agent.py
│       ├── stub_persistence.py
│       ├── stub_event_bus.py
│       ├── stub_filesystem.py
│       └── stub_clock.py
│
├── examples/
│   ├── basic_workflow/
│   │   ├── loopengine.toml
│   │   └── README.md
│   ├── custom_agent_adapter/
│   │   └── README.md
│   ├── custom_plugin/
│   │   └── README.md
│   └── cicd_integration/
│       └── README.md
│
└── docs/
    ├── architecture.md
    ├── plugin_development.md
    ├── agent_integration.md
    ├── configuration_reference.md
    └── diagrams/
```

---

## 2. Module Responsibilities

### Core — Domain Layer

| Module | Responsibility |
|---|---|
| `core.domain.entities.workflow` | **Aggregate root.** Owns lifecycle state machine (CREATED → RUNNING → ITERATING → COMPLETED/FAILED). Contains phases and artifacts. Enforces invariants on transitions. |
| `core.domain.entities.phase` | Represents a single workflow phase (e.g., PLAN, EXECUTE). Owns ordered steps. Tracks phase-level status. |
| `core.domain.entities.step` | Atomic execution unit within a phase. Carries a prompt, expects a typed result. Smallest unit of agent interaction. |
| `core.domain.entities.artifact` | Immutable record of phase output. Typed by kind (CODE, TEST_RESULT, DOC, METRIC). Versioned and linked to producing phase. |
| `core.domain.entities.session` | Runtime context for a single workflow execution. Carries accumulated state, iteration count, and timing. |
| `core.domain.value_objects.*` | Immutable, self-validating types. Identity wrappers, enums, typed containers. No behavior — pure data contracts. |
| `core.domain.events.*` | Domain events raised by entities. All cross-module communication flows through events. Immutable, timestamped, carry full context. |
| `core.domain.exceptions.*` | Domain-specific exceptions. Raised to signal invariant violations or illegal state transitions. |
| `core.domain.policies.*` | Pure business rules as strategy objects. Convergence, retry, and escalation logic is pluggable via these interfaces. |
| `core.domain.services.workflow_engine` | **Central orchestrator.** Drives the phase state machine. Calls phase scheduler, convergence analyzer, and context assembler. Contains zero I/O — delegates through ports. |
| `core.domain.services.phase_scheduler` | Determines the next phase based on current state, results, and policies. Handles phase skip/insert logic. |
| `core.domain.services.convergence_analyzer` | Evaluates whether a workflow has converged or needs another iteration. Consults convergence policy. |
| `core.domain.services.context_assembler` | Builds the context payload (prompt + state) that an agent receives. Pure transformation of domain state → agent-compatible format. |
| `core.domain.services.artifact_analyzer` | Extracts signals from artifacts (e.g., test pass rate, lint error count). Pure analysis — no side effects. |

### Core — Ports

| Port | Direction | Purpose |
|---|---|---|
| `ports.inbound.orchestrator_port` | Inbound | Public API for starting, stopping, and querying workflows. Implemented by application services. |
| `ports.inbound.workflow_command` | Inbound | CQRS write side — all mutations go through command objects. |
| `ports.inbound.workflow_query` | Inbound | CQRS read side — status queries and artifact retrieval. |
| `ports.outbound.agent_port` | Outbound | Abstract contract for invoking any AI agent. Implementations: Claude, OpenAI, Copilot, custom. |
| `ports.outbound.persistence_port` | Outbound | Save/retrieve workflow state. Implementations: JSON, SQLite, in-memory. |
| `ports.outbound.event_bus_port` | Outbound | Publish domain events to subscribers. Implementations: in-memory, async. |
| `ports.outbound.filesystem_port` | Outbound | Read/write project files. Abstracts over local FS, git worktrees, etc. |
| `ports.outbound.clock_port` | Outbound | Time abstraction for deterministic testing. |
| `ports.outbound.id_port` | Outbound | ID generation abstraction (UUID, ULID, etc.). |
| `ports.outbound.plugin_registry_port` | Outbound | Query loaded plugins and their capabilities. |

### Application Layer

| Module | Responsibility |
|---|---|
| `application.use_cases.*` | Single-responsibility operations. Each use case orchestrates one business action by calling domain services and outbound ports. Thin — no business logic. |
| `application.services.workflow_application_service` | Coordinates use cases, manages transactional boundaries, translates between DTOs and domain objects. |
| `application.services.agent_orchestration_service` | Manages agent lifecycle: selection, invocation, timeout handling, response normalization. |
| `application.services.reporting_service` | Aggregates domain data into status reports and metrics summaries. |
| `application.dto.*` | Data Transfer Objects. Serialization boundaries between layers. Never leak domain entities outward. |
| `application.event_handlers.*` | React to domain events to trigger cross-cutting concerns: logging, notifications, persistence snapshots. |

### Adapters Layer

| Module | Responsibility |
|---|---|
| `adapters.inbound.cli` | Click/Typer CLI application. Parses user input, invokes use cases, formats output. |
| `adapters.inbound.api` | FastAPI/Flask REST server. Exposes workflow management as HTTP endpoints. |
| `adapters.inbound.webhook` | Receives external triggers (CI/CD completion, git push, etc.) and routes to use cases. |
| `adapters.outbound.agents.*` | Each adapter implements `agent_port` for a specific AI agent. Handles API auth, prompt formatting, response parsing, rate limiting. |
| `adapters.outbound.persistence.*` | Implements `persistence_port` for different storage backends. JSON for dev, SQLite for production, in-memory for tests. |
| `adapters.outbound.validation.*` | Implements validation adapters. Each wraps an external tool (linter, type checker, test runner) behind a uniform interface. |
| `adapters.outbound.filesystem` | Implements `filesystem_port` for local filesystem access. Handles path normalization, file watching. |
| `adapters.outbound.events.*` | Event bus implementations. In-memory for synchronous testing, async for production. |
| `adapters.outbound.cicd` | Integrates with CI/CD systems to trigger pipelines and read results. |

### Plugins

| Module | Responsibility |
|---|---|
| `plugins.plugin_base` | Abstract `Plugin` base class. Defines lifecycle hooks: `on_load`, `on_activate`, `on_deactivate`, `on_unload`. |
| `plugins.plugin_loader` | Discovers plugins via `pyproject.toml` entry points and convention-based directory scanning. Handles import errors gracefully. |
| `plugins.plugin_registry` | Runtime store of loaded plugins. Maps plugin IDs to instances and their registered hooks/capabilities. |
| `plugins.hook_types` | Enum of all available hook points: `BEFORE_PHASE`, `AFTER_PHASE`, `ON_VALIDATION`, `ON_REFLECTION`, `ON_ERROR`, etc. |
| `plugins.hook_dispatcher` | Invokes registered hooks in priority order. Handles hook errors without crashing the workflow. |
| `plugins.builtin.*` | First-party plugins shipped with LoopEngine. Coverage analysis, security scanning, documentation generation, metrics collection. |

### Infrastructure

| Module | Responsibility |
|---|---|
| `infrastructure.config.settings` | Pydantic Settings class. Validates and loads configuration from file + env vars. |
| `infrastructure.config.schema` | Typed configuration schema. Defines all valid `loopengine.toml` keys. |
| `infrastructure.config.loader` | Reads TOML/YAML config files, merges with env overrides, produces `Settings`. |
| `infrastructure.container.di_container` | Dependency Injection container. Wires all port implementations. Single composition root. |
| `infrastructure.logging` | Structured JSON logging with context propagation. |
| `infrastructure.telemetry` | OpenTelemetry metrics and tracing hooks. |

### Shared

| Module | Responsibility |
|---|---|
| `shared.types` | Generic type aliases (`Result`, `EventHandler`, etc.). |
| `shared.immutable` | Base class for frozen/immutable value objects. |
| `shared.serialization` | Safe JSON serialization/deserialization helpers with type validation. |

---

## 3. Dependency Graph

```
                    ┌──────────────────────────────┐
                    │       INFRASTRUCTURE          │
                    │  config · container · logging  │
                    │         · telemetry            │
                    └──────────┬───────────────────┘
                               │ wires adapters into ports
                               ▼
                    ┌──────────────────────────────┐
                    │          ADAPTERS             │
                    │  inbound: cli · api · webhook │
                    │  outbound: agents · persist   │
                    │  · validation · events · fs   │
                    └──────────┬───────────────────┘
                               │ implements port interfaces
                               ▼
          ┌──────────────────────────────────────────┐
          │              APPLICATION                 │
          │  use_cases · services · dto · handlers   │
          │  calls domain services + outbound ports   │
          └────────────────┬─────────────────────────┘
                           │ uses domain entities + services
                           ▼
  ┌──────────────────────────────────────────────────────┐
  │                     DOMAIN (CORE)                    │
  │  entities · value_objects · events · exceptions      │
  │  policies · services · PORTS (inbound & outbound)    │
  │                                                      │
  │  ← depends on NOTHING external →                     │
  └──────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │                    SHARED KERNEL                     │
  │  types · immutable · serialization                   │
  │  ← depended upon by ALL layers →                     │
  └──────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────┐
  │                   PLUGIN SYSTEM                      │
  │  plugin_base · loader · registry · hooks             │
  │  ← uses ports + domain, loaded by infrastructure →   │
  └──────────────────────────────────────────────────────┘
```

**Dependency Direction Rule:** Arrows always point **inward** toward the Domain core. The Domain layer has **zero** dependencies on any outer layer.

**Detailed import rules:**

| Importer | May import from |
|---|---|
| `core.domain.*` | `core.domain.*` only (plus `shared`) |
| `core.ports.*` | `core.domain.value_objects`, `core.domain.entities`, `core.domain.events`, `shared` |
| `application.*` | `core.*` (full), `shared` |
| `adapters.*` | `core.ports.*`, `application.*`, `shared`, external libraries |
| `plugins.*` | `core.ports.*`, `core.domain.*`, `shared` |
| `infrastructure.*` | `adapters.*`, `application.*`, `core.ports.*`, `plugins.*`, `shared`, external libraries |

---

## 4. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER / CI / WEBHOOK                          │
│                           (External)                                │
└──────────┬──────────────────┬───────────────────┬──────────────────┘
           │                  │                   │
           ▼                  ▼                   ▼
┌─────────────────┐ ┌──────────────┐ ┌─────────────────────┐
│   CLI Adapter   │ │  API Adapter  │ │  Webhook Adapter    │
│  (inbound)      │ │  (inbound)    │ │  (inbound)          │
│  typer/click    │ │  FastAPI      │ │  HTTP receiver      │
└────────┬────────┘ └──────┬───────┘ └──────────┬──────────┘
         │                 │                     │
         └────────────┬────┘─────────────────────┘
                      │  calls Inbound Ports
                      ▼
         ┌────────────────────────────────┐
         │      APPLICATION LAYER         │
         │                                │
         │  ┌──────────────────────────┐  │
         │  │    Use Cases             │  │
         │  │  StartWorkflow           │  │
         │  │  RunPhase                │  │
         │  │  ExecuteFullCycle        │  │
         │  │  ValidateArtifact        │  │
         │  │  ReflectAndDecide        │  │
         │  │  IterateWorkflow         │  │
         │  │  GetWorkflowStatus       │  │
         │  └────────────┬─────────────┘  │
         │               │                │
         │  ┌────────────▼─────────────┐  │
         │  │  Application Services    │  │
         │  │  WorkflowAppService      │  │
         │  │  AgentOrchestrationSvc   │  │
         │  │  ReportingService        │  │
         │  └────────────┬─────────────┘  │
         │               │                │
         │  ┌────────────▼─────────────┐  │
         │  │  Event Handlers          │  │
         │  │  (side-effects on events)│  │
         │  └──────────────────────────┘  │
         └───────────┬─────────┬──────────┘
                     │         │
        ┌────────────┘         └────────────┐
        │ uses domain services               │ calls outbound ports
        ▼                                    ▼
┌───────────────────────────────────────────────────────────────┐
│                     DOMAIN LAYER                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                     Entities                            │  │
│  │  Workflow ──┬── Phase ──┬── Step                        │  │
│  │             │           └── Artifact                    │  │
│  │             └── Session                                 │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                Value Objects                            │  │
│  │  WorkflowId · PhaseType · PhaseStatus · WorkflowStatus  │  │
│  │  ArtifactKind · AgentConfig · Severity · Result[T,E]   │  │
│  │  Prompt · ContextPayload                                │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Domain Services                            │  │
│  │  ┌───────────────┐  ┌────────────────┐                 │  │
│  │  │WorkflowEngine │  │PhaseScheduler  │                 │  │
│  │  │  (FSM core)   │─▶│ (next phase?)  │                 │  │
│  │  └───────┬───────┘  └────────────────┘                 │  │
│  │          │                                               │  │
│  │  ┌───────▼───────────┐  ┌──────────────────┐           │  │
│  │  │ConvergenceAnalyzer│  │ContextAssembler  │           │  │
│  │  │  (iterate? yes/no)│  │(state→prompt)    │           │  │
│  │  └───────────────────┘  └──────────────────┘           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │               Ports (Interfaces)                        │  │
│  │                                                         │  │
│  │  INBOUND (implemented by Application)                   │  │
│  │  ┌────────────────┐ ┌──────────────┐ ┌──────────────┐  │  │
│  │  │OrchestratorPort│ │WorkflowCmd   │ │WorkflowQuery │  │  │
│  │  └────────────────┘ └──────────────┘ └──────────────┘  │  │
│  │                                                         │  │
│  │  OUTBOUND (implemented by Adapters)                     │  │
│  │  ┌─────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │AgentPort│ │PersistPort │ │EventBus  │ │FS Port   │ │  │
│  │  └────┬────┘ └─────┬──────┘ └────┬─────┘ └────┬─────┘ │  │
│  └───────┼────────────┼─────────────┼─────────────┼───────┘  │
└──────────┼────────────┼─────────────┼─────────────┼──────────┘
           │            │             │             │
           ▼            ▼             ▼             ▼
┌───────────────────────────────────────────────────────────────┐
│                    ADAPTER LAYER (outbound)                    │
│                                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ Agent Adapters│ │ Persistence  │ │  Event Bus           │  │
│  │ ┌───────────┐│ │ ┌───────────┐│ │  ┌─────────────────┐ │  │
│  │ │ Claude    ││ │ │ JSON File ││ │  │ InMemory EventBus│ │  │
│  │ ├───────────┤│ │ ├───────────┤│ │  ├─────────────────┤ │  │
│  │ │ OpenAI    ││ │ │ SQLite    ││ │  │ Async EventBus   │ │  │
│  │ ├───────────┤│ │ ├───────────┤│ │  └─────────────────┘ │  │
│  │ │ Copilot   ││ │ │ InMemory  ││ │                       │  │
│  │ ├───────────┤│ │ └───────────┘│ │  ┌──────────────────┐│  │
│  │ │ Gemini    ││ └──────────────┘ │  │Validation Adaptrs││  │
│  │ ├───────────┤│                   │  │ ┌──────────────┐ ││  │
│  │ │ Custom    ││ ┌──────────────┐ │  │ │Linter        │ ││  │
│  │ └───────────┘│ │ Filesystem   │ │  │ ├──────────────┤ ││  │
│  └──────────────┘ │ Local FS     │ │  │ │Type Checker  │ ││  │
│                    └──────────────┘ │  │ ├──────────────┤ ││  │
│                                     │  │ │Test Runner   │ ││  │
│                                     │  │ ├──────────────┤ ││  │
│                                     │  │ │Security Scan │ ││  │
│                                     │  │ └──────────────┘ ││  │
│                                     │  └──────────────────┘│  │
│                                     └──────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagram

### Primary: Full Workflow Lifecycle

```
USER
  │
  │  loopengine run --config loopengine.toml
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: INITIALIZATION                                              │
│                                                                     │
│  CLI Adapter                                                        │
│    ├── reads loopengine.toml (Config Loader → Settings)             │
│    ├── instantiates DI Container (wires adapters → ports)           │
│    ├── loads plugins (Plugin Loader → Plugin Registry)              │
│    └── calls StartWorkflow use case                                 │
│         ├── creates Workflow entity (aggregate root)                │
│         ├── creates Session entity (iteration=0)                    │
│         ├── persists initial state (PersistencePort)                │
│         ├── raises WorkflowCreated event (EventBusPort)             │
│         └── returns WorkflowId to CLI                               │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: ORCHESTRATION LOOP                                          │
│                                                                     │
│  WorkflowEngine.run_cycle(session)                                  │
│    │                                                                │
│    ├───► PhaseScheduler.next_phase(workflow)                        │
│    │     │  inspects current state                                  │
│    │     │  returns PhaseType (e.g., PLAN)                          │
│    │     │                                                          │
│    │     ▼                                                          │
│    │   ┌─────────────────────────────────────────────────────────┐  │
│    │   │  PHASE: PLAN                                            │  │
│    │   │                                                         │  │
│    │   │  ContextAssembler.build_context(workflow, PLAN)         │  │
│    │   │    └── gathers artifacts, state, instructions           │  │
│    │   │    └── produces ContextPayload                          │  │
│    │   │                                                         │  │
│    │   │  EventBusPort.publish(PhaseStarted)                     │  │
│    │   │  HookDispatcher.dispatch(BEFORE_PHASE, phase=PLAN)     │  │
│    │   │                                                         │  │
│    │   │  AgentPort.invoke(agent_config, context_payload)        │  │
│    │   │    └── ClaudeAdapter formats prompt                     │  │
│    │   │    └── calls Claude API                                 │  │
│    │   │    └── parses response                                  │  │
│    │   │    └── returns AgentResponse                            │  │
│    │   │                                                         │  │
│    │   │  creates Artifact (kind=PLAN, content=...)              │  │
│    │   │  attaches Artifact to Phase                             │  │
│    │   │  Phase.status = COMPLETED                               │  │
│    │   │                                                         │  │
│    │   │  EventBusPort.publish(PhaseCompleted, ValidationReq'd)  │  │
│    │   │  HookDispatcher.dispatch(AFTER_PHASE, phase=PLAN)      │  │
│    │   └─────────────────────────────────────────────────────────┘  │
│    │                                                                │
│    ├───► PhaseScheduler.next_phase(workflow)                        │
│    │     returns PhaseType: EXECUTE                                 │
│    │                                                                │
│    │   ┌─────────────────────────────────────────────────────────┐  │
│    │   │  PHASE: EXECUTE                                         │  │
│    │   │  (same pattern: context → agent → artifact)             │  │
│    │   │  produces Artifact(kind=CODE, content=generated_code)   │  │
│    │   └─────────────────────────────────────────────────────────┘  │
│    │                                                                │
│    ├───► PhaseScheduler.next_phase(workflow)                        │
│    │     returns PhaseType: VALIDATE                                │
│    │                                                                │
│    │   ┌─────────────────────────────────────────────────────────┐  │
│    │   │  PHASE: VALIDATE                                        │  │
│    │   │                                                         │  │
│    │   │  FilesystemPort.write(code_artifact) → project files    │  │
│    │   │                                                         │  │
│    │   │  run validators in parallel:                            │  │
│    │   │    ├── LinterValidator.validate()  → LintResult         │  │
│    │   │    ├── TypeChecker.validate()      → TypeResult         │  │
│    │   │    ├── TestRunner.validate()       → TestResult         │  │
│    │   │    └── SecurityScanner.validate()  → SecResult          │  │
│    │   │                                                         │  │
│    │   │  aggregates into ValidationReport                       │  │
│    │   │  Artifact(kind=VALIDATION, content=report)              │  │
│    │   │                                                         │  │
│    │   │  EventBusPort.publish(ValidationCompleted)              │  │
│    │   └─────────────────────────────────────────────────────────┘  │
│    │                                                                │
│    ├───► PhaseScheduler.next_phase(workflow)                        │
│    │     returns PhaseType: REFLECT                                 │
│    │                                                                │
│    │   ┌─────────────────────────────────────────────────────────┐  │
│    │   │  PHASE: REFLECT                                         │  │
│    │   │                                                         │  │
│    │   │  ContextAssembler.build_reflection_context(workflow)     │  │
│    │   │    └── includes all artifacts from this iteration       │  │
│    │   │                                                         │  │
│    │   │  AgentPort.invoke(reflection_prompt)                    │  │
│    │   │    └── agent analyzes results, identifies gaps          │  │
│    │   │    └── returns reflection with suggestions              │  │
│    │   │                                                         │  │
│    │   │  Artifact(kind=REFLECTION, content=analysis)            │  │
│    │   │                                                         │  │
│    │   │  ConvergenceAnalyzer.evaluate(workflow)                 │  │
│    │   │    ├── checks validation results                        │  │
│    │   │    ├── checks reflection recommendations                │  │
│    │   │    ├── consults convergence policy                      │  │
│    │   │    ├── checks max iterations                            │  │
│    │   │    └── returns ConvergeResult:                          │  │
│    │   │         ├── CONVERGED → workflow complete               │  │
│    │   │         └── NOT_CONVERGED → iteration_needed + reason   │  │
│    │   │                                                         │  │
│    │   │  EventBusPort.publish(ReflectionCompleted)              │  │
│    │   └─────────────────────────────────────────────────────────┘  │
│    │                                                                │
│    ├───► ConvergenceAnalyzer result: NOT_CONVERGED                  │
│    │     session.iteration += 1                                     │
│    │     PersistencePort.save(session)                              │
│    │     EventBusPort.publish(IterationDecided)                     │
│    │                                                                │
│    │     ◄──── loop back to WorkflowEngine.run_cycle ─────         │
│    │                                                                │
│    │     NEXT ITERATION:                                           │
│    │     PhaseScheduler now considers reflection feedback           │
│    │     may skip PLAN, go directly to EXECUTE with fixes          │
│    │                                                                │
│    ├───► Eventually: ConvergenceAnalyzer returns CONVERGED          │
│    │                                                                │
│    │   EventBusPort.publish(WorkflowCompleted)                     │
│    │   PersistencePort.save(final state)                           │
│    │   HookDispatcher.dispatch(WORKFLOW_COMPLETE)                  │
│    └────                                                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 3: OUTPUT                                                      │
│                                                                     │
│  CLI Adapter                                                        │
│    ├── retrieves final status from WorkflowQuery port               │
│    ├── formats output (console/json)                                │
│    └── displays: workflow complete, N iterations, artifacts summary │
└─────────────────────────────────────────────────────────────────────┘
```

### Simplified Sequence

```
┌──────┐    ┌──────────┐    ┌─────────┐    ┌───────────┐    ┌───────┐
│ User │    │   CLI    │    │  App    │    │  Domain   │    │ Agent │
│      │    │ Adapter  │    │  Layer  │    │  Engine   │    │Adaptr │
└──┬───┘    └────┬─────┘    └────┬────┘    └─────┬─────┘    └───┬───┘
   │  run        │               │               │              │
   │────────────►│  start        │               │              │
   │             │──────────────►│  create       │              │
   │             │               │──────────────►│              │
   │             │               │               │  persist     │
   │             │               │               │──┐           │
   │             │               │               │◄─┘           │
   │             │               │               │              │
   │             │               │               │ ◄─ LOOP ──► │
   │             │               │               │              │
   │             │               │    plan       │              │
   │             │               │──────────────►│  invoke      │
   │             │               │               │─────────────►│
   │             │               │               │◄─────────────│
   │             │               │               │              │
   │             │               │    execute    │              │
   │             │               │──────────────►│  invoke      │
   │             │               │               │─────────────►│
   │             │               │               │◄─────────────│
   │             │               │               │              │
   │             │               │    validate   │              │
   │             │               │──────────────►│  run tools   │
   │             │               │               │──┐           │
   │             │               │               │◄─┘           │
   │             │               │               │              │
   │             │               │    reflect    │              │
   │             │               │──────────────►│  invoke      │
   │             │               │               │─────────────►│
   │             │               │               │◄─────────────│
   │             │               │               │              │
   │             │               │    converge?  │              │
   │             │               │──────────────►│              │
   │             │               │    iterate!   │              │
   │             │               │◄──────────────│              │
   │             │               │    └──── loop ┘              │
   │             │               │               │              │
   │             │               │    converged  │              │
   │             │               │◄──────────────│              │
   │             │  done         │               │              │
   │             │◄──────────────│               │              │
   │  output     │               │               │              │
   │◄────────────│               │               │              │
```

---

## 6. Package Organization

### Distribution Package

```
loopengine                          # Top-level PyPI package
├── loopengine.core                 # python -m loopengine.core
│   ├── loopengine.core.domain      # Domain entities, VOs, events, policies
│   ├── loopengine.core.ports       # Port interfaces (inbound + outbound)
│   └── loopengine.core.services    # Domain services
│
├── loopengine.application          # Application layer
│   ├── loopengine.application.use_cases
│   ├── loopengine.application.services
│   ├── loopengine.application.dto
│   └── loopengine.application.event_handlers
│
├── loopengine.adapters             # Adapter implementations
│   ├── loopengine.adapters.inbound
│   │   ├── loopengine.adapters.inbound.cli
│   │   ├── loopengine.adapters.inbound.api
│   │   └── loopengine.adapters.inbound.webhook
│   └── loopengine.adapters.outbound
│       ├── loopengine.adapters.outbound.agents
│       ├── loopengine.adapters.outbound.persistence
│       ├── loopengine.adapters.outbound.validation
│       ├── loopengine.adapters.outbound.filesystem
│       ├── loopengine.adapters.outbound.events
│       ├── loopengine.adapters.outbound.clock
│       └── loopengine.adapters.outbound.cicd
│
├── loopengine.plugins              # Plugin system
│   └── loopengine.plugins.builtin  # Shipped plugins
│
├── loopengine.infrastructure       # Infrastructure
│   ├── loopengine.infrastructure.config
│   ├── loopengine.infrastructure.container
│   ├── loopengine.infrastructure.logging
│   └── loopengine.infrastructure.telemetry
│
└── loopengine.shared               # Shared kernel
```

### pyproject.toml Entry Points (Plugin System)

```toml
[project.entry-points."loopengine.plugins"]
coverage_enhancer  = "loopengine.plugins.builtin.coverage_enhancer:CoveragePlugin"
security_hardener  = "loopengine.plugins.builtin.security_hardener:SecurityPlugin"
doc_generator      = "loopengine.plugins.builtin.doc_generator:DocPlugin"
metrics_collector  = "loopengine.plugins.builtin.metrics_collector:MetricsPlugin"

[project.entry-points."loopengine.agents"]
claude  = "loopengine.adapters.outbound.agents.claude_adapter:ClaudeAdapter"
openai  = "loopengine.adapters.outbound.agents.openai_adapter:OpenAIAdapter"
copilot = "loopengine.adapters.outbound.agents.copilot_adapter:CopilotAdapter"
gemini  = "loopengine.adapters.outbound.agents.gemini_adapter:GeminiAdapter"

[project.entry-points."loopengine.validators"]
linter      = "loopengine.adapters.outbound.validation.linter_validator:LinterValidator"
type_checker = "loopengine.adapters.outbound.validation.type_checker_validator:TypeCheckerValidator"
test_runner = "loopengine.adapters.outbound.validation.test_runner_validator:TestRunnerValidator"
security    = "loopengine.adapters.outbound.validation.security_scanner_validator:SecurityScannerValidator"
```

### DI Container Wiring Summary

```
┌─────────────────────────────────────────────────────────┐
│                    DI CONTAINER                         │
│                  (Composition Root)                     │
│                                                         │
│  ┌──────────────────┐     ┌──────────────────────────┐  │
│  │  Port Interface  │────▶│  Adapter Implementation  │  │
│  ├──────────────────┤     ├──────────────────────────┤  │
│  │ AgentPort        │────▶│ ClaudeAdapter (default)  │  │
│  │ PersistencePort  │────▶│ JsonFileStore (default)  │  │
│  │ EventBusPort     │────▶│ InMemoryEventBus         │  │
│  │ FilesystemPort   │────▶│ LocalFilesystem          │  │
│  │ ClockPort        │────▶│ SystemClock              │  │
│  │ IdPort           │────▶│ UUIDGenerator            │  │
│  │ OrchestratorPort │────▶│ WorkflowAppService       │  │
│  │ PluginRegPort    │────▶│ PluginRegistry           │  │
│  └──────────────────┘     └──────────────────────────┘  │
│                                                         │
│  All adapters are swappable via config or runtime.      │
│  Test mode: swap all for in-memory / stub versions.     │
└─────────────────────────────────────────────────────────┘
```

### Architectural Invariants

| # | Invariant | Enforced by |
|---|---|---|
| 1 | Domain layer has zero external dependencies | Import rules + linting |
| 2 | All agent interaction goes through `AgentPort` | No direct imports to adapter code from application |
| 3 | Entities are the only source of state mutations | Domain services operate on entities; DTOs are transient |
| 4 | All cross-module communication uses domain events | EventBusPort is the sole inter-module channel |
| 5 | Configuration is immutable after container wiring | Pydantic `frozen=True` on Settings |
| 6 | Every adapter is replaceable for testing | Port interfaces + in-memory stubs |
| 7 | Plugins cannot break core invariants | Plugin API exposed only through ports, not internal APIs |
| 8 | Phase transitions follow a strict state machine | `WorkflowEngine` validates all transitions |

### Recommended Libraries

| Concern | Library |
|---|---|
| CLI | `typer` |
| API | `fastapi` + `uvicorn` |
| Config | `pydantic-settings` + `tomli` |
| DI | `dependency-injector` or manual wiring |
| Events | Custom in-memory, optional `dishka` or `event-bus` |
| Testing | `pytest` + `pytest-asyncio` + `pytest-cov` |
| Linting | `ruff` |
| Type checking | `pyright` |
| Async | `asyncio` (optional — core can be sync, adapters async) |
| Logging | `structlog` |
| ID generation | `uuid` (stdlib) or `ulid-py` |
