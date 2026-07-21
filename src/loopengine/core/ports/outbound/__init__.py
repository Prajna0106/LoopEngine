"""Outbound ports — contracts driven by adapters.

Each module defines a single port interface following the Interface
Segregation Principle. Adapters implement these; domain services depend
on them.
"""

from loopengine.core.ports.outbound.agent_port import AgentResponse, BaseAgent
from loopengine.core.ports.outbound.executor_port import ExecutionResult, Executor
from loopengine.core.ports.outbound.logger_port import Logger
from loopengine.core.ports.outbound.memory_store_port import MemoryStore
from loopengine.core.ports.outbound.metrics_port import MetricsCollector
from loopengine.core.ports.outbound.planner_port import (
    Planner,
    PlanPhase,
    PlanResult,
    PlanStep,
    StepComplexity,
    StepPriority,
)
from loopengine.core.ports.outbound.plugin_registry_port import (
    BasePlugin,
    PluginInfo,
    PluginMetadata,
    PluginRegistry,
    PluginState,
)
from loopengine.core.ports.outbound.prompt_port import (
    PromptProvider,
    PromptRegistry,
    PromptTemplate,
    PromptVersion,
)
from loopengine.core.ports.outbound.reflection_port import (
    ReflectionDecision,
    ReflectionEngine,
    ReflectionResult,
)
from loopengine.core.ports.outbound.reviewer_port import (
    ReviewComment,
    Reviewer,
    ReviewResult,
    ReviewVerdict,
)
from loopengine.core.ports.outbound.validator_port import (
    Severity,
    ValidationIssue,
    ValidationResult,
    Validator,
)

__all__ = [
    "AgentResponse",
    "BaseAgent",
    "BasePlugin",
    "ExecutionResult",
    "Executor",
    "Logger",
    "MemoryStore",
    "MetricsCollector",
    "PlanPhase",
    "PlanResult",
    "PlanStep",
    "Planner",
    "PluginInfo",
    "PluginMetadata",
    "PluginRegistry",
    "PluginState",
    "PromptProvider",
    "PromptRegistry",
    "PromptTemplate",
    "PromptVersion",
    "ReflectionDecision",
    "ReflectionEngine",
    "ReflectionResult",
    "ReviewComment",
    "ReviewResult",
    "ReviewVerdict",
    "Reviewer",
    "Severity",
    "StepComplexity",
    "StepPriority",
    "ValidationIssue",
    "ValidationResult",
    "Validator",
]
