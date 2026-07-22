"""Test factories for domain models.

Provides factory functions for creating test instances of all domain
models. Uses keyword arguments with sensible defaults for easy customization.
"""

from __future__ import annotations

import uuid
from typing import Any

from loopengine.core.ports.outbound.executor_port import ExecutionResult
from loopengine.core.ports.outbound.memory_store_port import (
    StoredExecution,
    StoredProjectMeta,
    StoredReflection,
    StoredReview,
)
from loopengine.core.ports.outbound.planner_port import (
    PlanPhase,
    PlanResult,
    PlanStep,
    StepComplexity,
    StepPriority,
)
from loopengine.core.ports.outbound.plugin_registry_port import (
    PluginMetadata,
)
from loopengine.core.ports.outbound.prompt_port import PromptTemplate
from loopengine.core.ports.outbound.reflection_port import (
    ReflectionDecision,
    ReflectionResult,
)
from loopengine.core.ports.outbound.reviewer_port import (
    ReviewResult,
    ReviewVerdict,
)
from loopengine.core.ports.outbound.validator_port import (
    Severity,
    ValidationIssue,
    ValidationResult,
)


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def plan_step(
    *,
    task_id: str | None = None,
    description: str = "Test step",
    dependencies: list[str] | None = None,
    priority: StepPriority = StepPriority.MEDIUM,
    complexity: StepComplexity = StepComplexity.MODERATE,
    acceptance_criteria: list[str] | None = None,
) -> PlanStep:
    return PlanStep(
        id=task_id or f"step-{_uid()}",
        description=description,
        dependencies=dependencies or [],
        priority=priority,
        complexity=complexity,
        acceptance_criteria=acceptance_criteria or ["Done"],
    )


def plan_result(
    *,
    goal: str = "Build feature X",
    steps: list[PlanStep] | None = None,
    phases: list[PlanPhase] | None = None,
    total_steps: int = 1,
    estimated_duration: str = "30 min",
) -> PlanResult:
    if steps is None:
        steps = [plan_step()]
    if phases is None:
        phases = [
            PlanPhase(name="implementation", steps=steps, description="Build"),
        ]
    return PlanResult(
        goal=goal,
        steps=steps,
        phases=phases,
        total_steps=total_steps,
        estimated_duration=estimated_duration,
    )


def execution_result(
    *,
    output: str = "Done",
    success: bool = True,
    artifacts: list[str] | None = None,
    duration_ms: float = 100.0,
    metadata: dict[str, Any] | None = None,
) -> ExecutionResult:
    return ExecutionResult(
        output=output,
        success=success,
        artifacts=artifacts or [],
        duration_ms=duration_ms,
        metadata=metadata or {},
    )


def reflection_result(
    *,
    decision: ReflectionDecision = ReflectionDecision.CONVERGED,
    reasoning: str = "All clear",
    issues: list[str] | None = None,
    suggestions: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ReflectionResult:
    return ReflectionResult(
        decision=decision,
        reasoning=reasoning,
        issues=issues or [],
        suggestions=suggestions or [],
        metadata=metadata or {},
    )


def validation_result(
    *,
    validator: str = "test",
    passed: bool = True,
    issues: list[ValidationIssue] | None = None,
    duration_ms: float = 50.0,
) -> ValidationResult:
    return ValidationResult(
        validator=validator,
        passed=passed,
        issues=issues or [],
        duration_ms=duration_ms,
    )


def validation_issue(
    *,
    message: str = "Issue found",
    file: str = "test.py",
    line: int = 1,
    severity: Severity = Severity.WARNING,
    rule: str = "test-rule",
) -> ValidationIssue:
    return ValidationIssue(
        message=message,
        file=file,
        line=line,
        severity=severity,
        rule=rule,
    )


def review_result(
    *,
    verdict: ReviewVerdict = ReviewVerdict.APPROVED,
    comments: list[dict[str, Any]] | None = None,
    summary: str = "Looks good",
    score: float = 8.0,
    metadata: dict[str, Any] | None = None,
) -> ReviewResult:
    return ReviewResult(
        verdict=verdict,
        comments=comments or [],
        summary=summary,
        score=score,
        metadata=metadata or {},
    )


def stored_execution(
    *,
    workflow_id: str | None = None,
    goal: str = "Build feature",
    status: str = "running",
    started_at: str = "2024-01-01T00:00:00",
    completed_at: str = "",
    iterations: int = 0,
    summary: str = "",
    metadata: dict[str, Any] | None = None,
) -> StoredExecution:
    return StoredExecution(
        workflow_id=workflow_id or f"wf-{_uid()}",
        goal=goal,
        status=status,
        started_at=started_at,
        completed_at=completed_at,
        iterations=iterations,
        summary=summary,
        metadata=metadata or {},
    )


def stored_reflection(
    *,
    execution_id: str | None = None,
    iteration: int = 1,
    decision: str = "CONVERGED",
    issues_count: int = 0,
    suggestions_count: int = 0,
    summary: str = "",
    metadata: dict[str, Any] | None = None,
) -> StoredReflection:
    return StoredReflection(
        execution_id=execution_id or f"exec-{_uid()}",
        iteration=iteration,
        decision=decision,
        issues_count=issues_count,
        suggestions_count=suggestions_count,
        summary=summary,
        metadata=metadata or {},
    )


def stored_review(
    *,
    execution_id: str | None = None,
    score: float = 8.0,
    verdict: str = "APPROVED",
    issues_count: int = 0,
    summary: str = "",
    metadata: dict[str, Any] | None = None,
) -> StoredReview:
    return StoredReview(
        execution_id=execution_id or f"exec-{_uid()}",
        score=score,
        verdict=verdict,
        issues_count=issues_count,
        summary=summary,
        metadata=metadata or {},
    )


def stored_project_meta(
    *,
    project_path: str | None = None,
    name: str = "test-project",
    language: str = "python",
    framework: str = "",
    metadata: dict[str, Any] | None = None,
) -> StoredProjectMeta:
    return StoredProjectMeta(
        project_path=project_path or f"test-project-{_uid()}",
        name=name,
        language=language,
        framework=framework,
        metadata=metadata or {},
    )


def prompt_template(
    *,
    name: str | None = None,
    content: str = "Hello {name}!",
    version: str = "1.0.0",
    variables: list[str] | None = None,
    tags: list[str] | None = None,
    description: str = "",
) -> PromptTemplate:
    return PromptTemplate(
        name=name or f"prompt-{_uid()}",
        content=content,
        version=version,
        variables=variables or [],
        tags=tags or [],
        description=description,
    )


def plugin_metadata(
    *,
    name: str | None = None,
    version: str = "1.0.0",
    author: str = "test",
    description: str = "Test plugin",
    dependencies: list[str] | None = None,
) -> PluginMetadata:
    return PluginMetadata(
        name=name or f"plugin-{_uid()}",
        version=version,
        author=author,
        description=description,
        dependencies=dependencies or [],
    )
