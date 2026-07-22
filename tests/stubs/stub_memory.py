"""In-memory stub for the memory store port."""

from __future__ import annotations

from loopengine.core.ports.outbound.memory_store_port import (
    ExecutionHistory,
    MemoryStore,
    ProjectMetaStore,
    ReflectionStore,
    ReviewStore,
    StoredExecution,
    StoredProjectMeta,
    StoredReflection,
    StoredReview,
)


class StubMemoryStore(MemoryStore):
    """Simple in-memory KV store."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, key: str) -> dict | None:
        return self._data.get(key)

    def put(self, key: str, value: dict) -> None:
        self._data[key] = dict(value)

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def list_keys(self, *, prefix: str = "") -> list[str]:
        if prefix:
            return [k for k in self._data if k.startswith(prefix)]
        return list(self._data)

    def clear(self) -> int:
        count = len(self._data)
        self._data.clear()
        return count

    def contains(self, key: str) -> bool:
        return key in self._data


class StubExecutionHistory(ExecutionHistory):
    """In-memory execution history for testing."""

    def __init__(self) -> None:
        self._records: dict[str, StoredExecution] = {}

    def save(self, execution: StoredExecution) -> None:
        self._records[execution.workflow_id] = execution

    def get(self, workflow_id: str) -> StoredExecution | None:
        return self._records.get(workflow_id)

    def list_all(self) -> list[StoredExecution]:
        return list(self._records.values())

    def delete(self, workflow_id: str) -> bool:
        return self._records.pop(workflow_id, None) is not None


class StubReflectionStore(ReflectionStore):
    """In-memory reflection store for testing."""

    def __init__(self) -> None:
        self._records: dict[str, list[StoredReflection]] = {}

    def save(self, reflection: StoredReflection) -> None:
        self._records.setdefault(reflection.execution_id, []).append(reflection)

    def list_for_execution(self, execution_id: str) -> list[StoredReflection]:
        return list(self._records.get(execution_id, []))

    def delete(self, execution_id: str) -> int:
        return len(self._records.pop(execution_id, []))


class StubReviewStore(ReviewStore):
    """In-memory review store for testing."""

    def __init__(self) -> None:
        self._records: dict[str, list[StoredReview]] = {}

    def save(self, review: StoredReview) -> None:
        self._records.setdefault(review.execution_id, []).append(review)

    def list_for_execution(self, execution_id: str) -> list[StoredReview]:
        return list(self._records.get(execution_id, []))

    def delete(self, execution_id: str) -> int:
        return len(self._records.pop(execution_id, []))


class StubProjectMetaStore(ProjectMetaStore):
    """In-memory project metadata store for testing."""

    def __init__(self) -> None:
        self._records: dict[str, StoredProjectMeta] = {}

    def save(self, meta: StoredProjectMeta) -> None:
        self._records[meta.project_path] = meta

    def get(self, project_path: str) -> StoredProjectMeta | None:
        return self._records.get(project_path)

    def list_all(self) -> list[StoredProjectMeta]:
        return list(self._records.values())

    def delete(self, project_path: str) -> bool:
        return self._records.pop(project_path, None) is not None
