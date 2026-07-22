# API Reference

## Port Interfaces

Port interfaces define contracts that adapters must implement. They live in
`core/ports/` and follow the Interface Segregation Principle.

### Outbound Ports

#### `BaseAgent`

```python
class BaseAgent(ABC):
    name: str  # property

    @abstractmethod
    def invoke(self, prompt: str, *, context: dict | None = None) -> AgentResponse: ...

    def is_available(self) -> bool: ...
```

#### `ExecutorPort`

```python
class ExecutorPort(ABC):
    @abstractmethod
    def execute(self, task: PlanStep) -> ExecutionResult: ...
```

#### `MetricsCollector`

```python
class MetricsCollector(ABC):
    @abstractmethod
    def increment(self, name: str, *, value: float = 1.0, tags: dict | None = None) -> None: ...

    @abstractmethod
    def gauge(self, name: str, value: float, *, tags: dict | None = None) -> None: ...

    @abstractmethod
    def timing(self, name: str, duration_ms: float, *, tags: dict | None = None) -> None: ...

    @abstractmethod
    def histogram(self, name: str, value: float, *, tags: dict | None = None) -> None: ...

    @abstractmethod
    def flush(self) -> None: ...

    def get_metrics(self) -> list[MetricPoint]: ...
    def reset(self) -> None: ...
```

#### `PluginRegistry`

```python
class PluginRegistry(ABC):
    @abstractmethod
    def register(self, plugin: BasePlugin) -> None: ...
    @abstractmethod
    def unregister(self, name: str) -> None: ...
    @abstractmethod
    def get(self, name: str) -> BasePlugin: ...
    @abstractmethod
    def list_plugins(self) -> list[PluginInfo]: ...
    @abstractmethod
    def enable(self, name: str) -> None: ...
    @abstractmethod
    def disable(self, name: str) -> None: ...
    @abstractmethod
    def is_enabled(self, name: str) -> bool: ...
    @abstractmethod
    def load_from_directory(self, path: str) -> list[str]: ...
```

#### `PromptRegistry`

```python
class PromptRegistry(ABC):
    @abstractmethod
    def register(self, template: PromptTemplate) -> None: ...
    @abstractmethod
    def get(self, name: str, *, version: str | None = None) -> PromptTemplate: ...
    @abstractmethod
    def list_templates(self) -> list[PromptTemplate]: ...
    @abstractmethod
    def render(self, name: str, **variables: str) -> str: ...
```

#### `MemoryStore`

```python
class MemoryStore(ABC):
    @abstractmethod
    def execution_history(self) -> ExecutionHistory: ...
    @abstractmethod
    def reflection_store(self) -> ReflectionStore: ...
    @abstractmethod
    def review_store(self) -> ReviewStore: ...
    @abstractmethod
    def project_meta_store(self) -> ProjectMetaStore: ...
```

### Inbound Ports

#### `OrchestratorPort`

```python
class OrchestratorPort(ABC):
    @abstractmethod
    def execute_workflow(self, config: LoopEngineConfig) -> WorkflowResult: ...
```

## Services

### `PlannerService`

```python
class PlannerService:
    def create_plan(self, goal: str, *, context: dict | None = None) -> PlanResult: ...
```

### `ExecutionEngine`

```python
class ExecutionEngine:
    def __init__(self, executor: ExecutorPort): ...
    def execute(self, plan: PlanResult, *, max_failures: int = 0) -> ExecutionReport: ...
```

### `ReflectionService`

```python
class ReflectionService:
    def reflect_on_results(
        self,
        *,
        _goal: str,
        results: list[dict],
        iteration: int,
    ) -> ReflectionResult: ...
```

## Adapters

### Agent Adapters

| Adapter | Agent | CLI |
|---------|-------|-----|
| `ClaudeAdapter` | Anthropic Claude | `claude` |
| `CodexAdapter` | OpenAI Codex | `codex` |
| `OpenCodeAdapter` | OpenCode | `opencode` |
| `GenericCLIAdapter` | Any CLI agent | configurable |

All extend `BaseAgentAdapter` which provides retry logic, timeout,
streaming, and structured logging.

### Persistence Adapters

| Adapter | Backend | Use Case |
|---------|---------|----------|
| `InMemoryStore` | In-memory | Testing |
| `SQLiteMemoryStore` | SQLite file | Production |

### Plugin Adapters

| Adapter | Description |
|---------|-------------|
| `InMemoryPluginRegistry` | In-memory plugin registry with filesystem discovery |

### Prompt Adapters

| Adapter | Description |
|---------|-------------|
| `InMemoryPromptRegistry` | In-memory registry with caching and versioning |
| `FilePromptProvider` | Loads `.md` prompt files from disk |

## Infrastructure

### DI Container

```python
from loopengine.infrastructure.container.di_container import Container

container = Container(settings)
container.register(MyInterface, MyImplementation)
instance = container.resolve(MyInterface)
```

### Structured Logger

```python
from loopengine.infrastructure.logging.structured_logger import StructuredLogger

logger = StructuredLogger()
logger.info("event_name", key="value")
logger.bind(session_id="abc123")
```

### Metrics

```python
from loopengine.infrastructure.telemetry.metrics import InMemoryMetrics, timed

metrics = InMemoryMetrics()
metrics.increment("requests")
metrics.gauge("connections", 5.0)
metrics.timing("latency", 42.0)

with timed(metrics, "operation"):
    do_work()
```

## Domain Models

### PlanStep

```python
@dataclass
class PlanStep:
    id: str
    name: str
    description: str
    dependencies: list[str]
    priority: StepPriority
    complexity: StepComplexity
    acceptance_criteria: list[str]
```

### ExecutionResult

```python
@dataclass
class ExecutionResult:
    output: str
    success: bool
    artifacts: list[str]
    duration_ms: float
    metadata: dict[str, Any]
```

### ReflectionResult

```python
@dataclass
class ReflectionResult:
    decision: ReflectionDecision  # CONVERGED | RETRY | FIX_AND_RETRY
    reasoning: str
    issues: list[str]
    suggestions: list[str]
    metadata: dict[str, Any]
```
