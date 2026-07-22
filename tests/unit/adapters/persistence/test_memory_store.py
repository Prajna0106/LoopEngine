"""Tests for persistence adapters (InMemory + SQLite)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from loopengine.adapters.outbound.persistence.in_memory_store import (
    InMemoryExecutionHistory,
    InMemoryProjectMetaStore,
    InMemoryReflectionStore,
    InMemoryReviewStore,
    InMemoryStore,
)
from loopengine.adapters.outbound.persistence.sqlite_store import (
    SQLiteExecutionHistory,
    SQLiteMemoryStore,
    SQLiteProjectMetaStore,
    SQLiteReflectionStore,
    SQLiteReviewStore,
)
from loopengine.core.ports.outbound.memory_store_port import (
    StoredExecution,
    StoredProjectMeta,
    StoredReflection,
    StoredReview,
)


class TestStoredExecution:
    def test_defaults(self) -> None:
        e = StoredExecution(
            workflow_id="w1",
            goal="test",
            status="running",
            started_at="2024-01-01",
        )
        assert e.workflow_id == "w1"
        assert e.iterations == 0
        assert e.metadata == {}

    def test_custom(self) -> None:
        e = StoredExecution(
            workflow_id="w1",
            goal="g",
            status="done",
            started_at="t",
            completed_at="t2",
            iterations=5,
            summary="s",
            metadata={"k": "v"},
        )
        assert e.iterations == 5
        assert e.metadata["k"] == "v"


class TestStoredReflection:
    def test_creation(self) -> None:
        r = StoredReflection(execution_id="e1", iteration=1, decision="RETRY")
        assert r.execution_id == "e1"
        assert r.issues_count == 0


class TestStoredReview:
    def test_creation(self) -> None:
        rv = StoredReview(execution_id="e1", score=8.5, verdict="APPROVED")
        assert rv.score == 8.5
        assert rv.verdict == "APPROVED"


class TestStoredProjectMeta:
    def test_creation(self) -> None:
        m = StoredProjectMeta(project_path="/proj", name="myproj", language="python")
        assert m.project_path == "/proj"
        assert m.language == "python"


class TestInMemoryStore:
    def test_put_and_get(self) -> None:
        s = InMemoryStore()
        s.put("k", {"a": 1})
        assert s.get("k") == {"a": 1}

    def test_get_not_found(self) -> None:
        s = InMemoryStore()
        assert s.get("missing") is None

    def test_delete_existing(self) -> None:
        s = InMemoryStore()
        s.put("k", {"a": 1})
        assert s.delete("k") is True
        assert s.get("k") is None

    def test_delete_nonexistent(self) -> None:
        s = InMemoryStore()
        assert s.delete("missing") is False

    def test_list_keys(self) -> None:
        s = InMemoryStore()
        s.put("a", {})
        s.put("b", {})
        s.put("c", {})
        assert sorted(s.list_keys()) == ["a", "b", "c"]

    def test_list_keys_with_prefix(self) -> None:
        s = InMemoryStore()
        s.put("user:1", {})
        s.put("user:2", {})
        s.put("post:1", {})
        assert sorted(s.list_keys(prefix="user:")) == ["user:1", "user:2"]

    def test_clear(self) -> None:
        s = InMemoryStore()
        s.put("a", {})
        s.put("b", {})
        assert s.clear() == 2
        assert s.list_keys() == []

    def test_contains(self) -> None:
        s = InMemoryStore()
        s.put("k", {})
        assert s.contains("k") is True
        assert s.contains("missing") is False

    def test_overwrite(self) -> None:
        s = InMemoryStore()
        s.put("k", {"v": 1})
        s.put("k", {"v": 2})
        assert s.get("k") == {"v": 2}

    def test_put_does_not_mutate_original(self) -> None:
        s = InMemoryStore()
        original = {"a": 1}
        s.put("k", original)
        original["b"] = 2
        assert s.get("k") == {"a": 1}


class TestSQLiteMemoryStore:
    def test_put_and_get(self) -> None:
        s = SQLiteMemoryStore()
        s.put("k", {"a": 1})
        assert s.get("k") == {"a": 1}
        s.close()

    def test_get_not_found(self) -> None:
        s = SQLiteMemoryStore()
        assert s.get("missing") is None
        s.close()

    def test_delete_existing(self) -> None:
        s = SQLiteMemoryStore()
        s.put("k", {"a": 1})
        assert s.delete("k") is True
        s.close()

    def test_delete_nonexistent(self) -> None:
        s = SQLiteMemoryStore()
        assert s.delete("missing") is False
        s.close()

    def test_list_keys(self) -> None:
        s = SQLiteMemoryStore()
        s.put("a", {})
        s.put("b", {})
        s.put("c", {})
        assert s.list_keys() == ["a", "b", "c"]
        s.close()

    def test_list_keys_with_prefix(self) -> None:
        s = SQLiteMemoryStore()
        s.put("user:1", {})
        s.put("user:2", {})
        s.put("post:1", {})
        assert s.list_keys(prefix="user:") == ["user:1", "user:2"]
        s.close()

    def test_clear(self) -> None:
        s = SQLiteMemoryStore()
        s.put("a", {})
        s.put("b", {})
        assert s.clear() == 2
        assert s.list_keys() == []
        s.close()

    def test_contains(self) -> None:
        s = SQLiteMemoryStore()
        s.put("k", {})
        assert s.contains("k") is True
        assert s.contains("missing") is False
        s.close()

    def test_persistence_to_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteMemoryStore(db_path)
            s1.put("k", {"v": 42})
            s1.close()
            s2 = SQLiteMemoryStore(db_path)
            assert s2.get("k") == {"v": 42}
            s2.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# InMemoryExecutionHistory
# ---------------------------------------------------------------------------


class TestInMemoryExecutionHistory:
    def test_save_and_get(self) -> None:
        h = InMemoryExecutionHistory()
        e = StoredExecution(workflow_id="w1", goal="g", status="running", started_at="t")
        h.save(e)
        assert h.get("w1") is e

    def test_get_not_found(self) -> None:
        h = InMemoryExecutionHistory()
        assert h.get("missing") is None

    def test_list_all(self) -> None:
        h = InMemoryExecutionHistory()
        h.save(StoredExecution(workflow_id="w1", goal="g1", status="running", started_at="t1"))
        h.save(StoredExecution(workflow_id="w2", goal="g2", status="done", started_at="t2"))
        assert len(h.list_all()) == 2

    def test_delete(self) -> None:
        h = InMemoryExecutionHistory()
        h.save(StoredExecution(workflow_id="w1", goal="g", status="running", started_at="t"))
        assert h.delete("w1") is True
        assert h.get("w1") is None

    def test_delete_nonexistent(self) -> None:
        h = InMemoryExecutionHistory()
        assert h.delete("missing") is False

    def test_overwrite(self) -> None:
        h = InMemoryExecutionHistory()
        h.save(StoredExecution(workflow_id="w1", goal="old", status="running", started_at="t"))
        h.save(StoredExecution(workflow_id="w1", goal="new", status="done", started_at="t2"))
        assert h.get("w1").goal == "new"


# ---------------------------------------------------------------------------
# SQLiteExecutionHistory
# ---------------------------------------------------------------------------


class TestSQLiteExecutionHistory:
    def test_save_and_get(self) -> None:
        h = SQLiteExecutionHistory()
        e = StoredExecution(workflow_id="w1", goal="g", status="running", started_at="t")
        h.save(e)
        result = h.get("w1")
        assert result is not None
        assert result.workflow_id == "w1"
        assert result.goal == "g"
        h.close()

    def test_get_not_found(self) -> None:
        h = SQLiteExecutionHistory()
        assert h.get("missing") is None
        h.close()

    def test_list_all(self) -> None:
        h = SQLiteExecutionHistory()
        h.save(StoredExecution(workflow_id="w1", goal="g1", status="r", started_at="t1"))
        h.save(StoredExecution(workflow_id="w2", goal="g2", status="d", started_at="t2"))
        assert len(h.list_all()) == 2
        h.close()

    def test_delete(self) -> None:
        h = SQLiteExecutionHistory()
        h.save(StoredExecution(workflow_id="w1", goal="g", status="r", started_at="t"))
        assert h.delete("w1") is True
        assert h.get("w1") is None
        h.close()

    def test_metadata_roundtrip(self) -> None:
        h = SQLiteExecutionHistory()
        e = StoredExecution(
            workflow_id="w1",
            goal="g",
            status="r",
            started_at="t",
            metadata={"key": "value", "nested": {"a": 1}},
        )
        h.save(e)
        result = h.get("w1")
        assert result.metadata == {"key": "value", "nested": {"a": 1}}
        h.close()

    def test_persistence_to_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            h1 = SQLiteExecutionHistory(db_path)
            h1.save(StoredExecution(workflow_id="w1", goal="g", status="r", started_at="t"))
            h1.close()
            h2 = SQLiteExecutionHistory(db_path)
            assert h2.get("w1") is not None
            h2.close()
        finally:
            Path(db_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# InMemoryReflectionStore
# ---------------------------------------------------------------------------


class TestInMemoryReflectionStore:
    def test_save_and_list(self) -> None:
        s = InMemoryReflectionStore()
        r = StoredReflection(execution_id="e1", iteration=1, decision="RETRY")
        s.save(r)
        assert len(s.list_for_execution("e1")) == 1

    def test_list_sorted_by_iteration(self) -> None:
        s = InMemoryReflectionStore()
        s.save(StoredReflection(execution_id="e1", iteration=3, decision="A"))
        s.save(StoredReflection(execution_id="e1", iteration=1, decision="B"))
        s.save(StoredReflection(execution_id="e1", iteration=2, decision="C"))
        iters = [r.iteration for r in s.list_for_execution("e1")]
        assert iters == [1, 2, 3]

    def test_list_empty(self) -> None:
        s = InMemoryReflectionStore()
        assert s.list_for_execution("missing") == []

    def test_delete(self) -> None:
        s = InMemoryReflectionStore()
        s.save(StoredReflection(execution_id="e1", iteration=1, decision="A"))
        s.save(StoredReflection(execution_id="e1", iteration=2, decision="B"))
        assert s.delete("e1") == 2
        assert s.list_for_execution("e1") == []

    def test_delete_nonexistent(self) -> None:
        s = InMemoryReflectionStore()
        assert s.delete("missing") == 0


# ---------------------------------------------------------------------------
# SQLiteReflectionStore
# ---------------------------------------------------------------------------


class TestSQLiteReflectionStore:
    def test_save_and_list(self) -> None:
        s = SQLiteReflectionStore()
        s.save(StoredReflection(execution_id="e1", iteration=1, decision="RETRY"))
        result = s.list_for_execution("e1")
        assert len(result) == 1
        assert result[0].decision == "RETRY"
        s.close()

    def test_list_sorted(self) -> None:
        s = SQLiteReflectionStore()
        s.save(StoredReflection(execution_id="e1", iteration=3, decision="A"))
        s.save(StoredReflection(execution_id="e1", iteration=1, decision="B"))
        iters = [r.iteration for r in s.list_for_execution("e1")]
        assert iters == [1, 3]
        s.close()

    def test_delete(self) -> None:
        s = SQLiteReflectionStore()
        s.save(StoredReflection(execution_id="e1", iteration=1, decision="A"))
        assert s.delete("e1") == 1
        assert s.list_for_execution("e1") == []
        s.close()


# ---------------------------------------------------------------------------
# InMemoryReviewStore
# ---------------------------------------------------------------------------


class TestInMemoryReviewStore:
    def test_save_and_list(self) -> None:
        s = InMemoryReviewStore()
        rv = StoredReview(execution_id="e1", score=9.0, verdict="APPROVED")
        s.save(rv)
        assert len(s.list_for_execution("e1")) == 1

    def test_list_empty(self) -> None:
        s = InMemoryReviewStore()
        assert s.list_for_execution("missing") == []

    def test_delete(self) -> None:
        s = InMemoryReviewStore()
        s.save(StoredReview(execution_id="e1", score=9.0, verdict="APPROVED"))
        s.save(StoredReview(execution_id="e1", score=7.0, verdict="CHANGES"))
        assert s.delete("e1") == 2
        assert s.list_for_execution("e1") == []


# ---------------------------------------------------------------------------
# SQLiteReviewStore
# ---------------------------------------------------------------------------


class TestSQLiteReviewStore:
    def test_save_and_list(self) -> None:
        s = SQLiteReviewStore()
        s.save(StoredReview(execution_id="e1", score=9.0, verdict="APPROVED"))
        result = s.list_for_execution("e1")
        assert len(result) == 1
        assert result[0].score == 9.0
        s.close()

    def test_delete(self) -> None:
        s = SQLiteReviewStore()
        s.save(StoredReview(execution_id="e1", score=9.0, verdict="APPROVED"))
        assert s.delete("e1") == 1
        s.close()


# ---------------------------------------------------------------------------
# InMemoryProjectMetaStore
# ---------------------------------------------------------------------------


class TestInMemoryProjectMetaStore:
    def test_save_and_get(self) -> None:
        s = InMemoryProjectMetaStore()
        m = StoredProjectMeta(project_path="/proj", name="myproj", language="python")
        s.save(m)
        assert s.get("/proj") is m

    def test_get_not_found(self) -> None:
        s = InMemoryProjectMetaStore()
        assert s.get("/missing") is None

    def test_list_all(self) -> None:
        s = InMemoryProjectMetaStore()
        s.save(StoredProjectMeta(project_path="/a"))
        s.save(StoredProjectMeta(project_path="/b"))
        assert len(s.list_all()) == 2

    def test_delete(self) -> None:
        s = InMemoryProjectMetaStore()
        s.save(StoredProjectMeta(project_path="/proj"))
        assert s.delete("/proj") is True
        assert s.get("/proj") is None

    def test_delete_nonexistent(self) -> None:
        s = InMemoryProjectMetaStore()
        assert s.delete("/missing") is False

    def test_overwrite(self) -> None:
        s = InMemoryProjectMetaStore()
        s.save(StoredProjectMeta(project_path="/proj", name="old"))
        s.save(StoredProjectMeta(project_path="/proj", name="new"))
        assert s.get("/proj").name == "new"


# ---------------------------------------------------------------------------
# SQLiteProjectMetaStore
# ---------------------------------------------------------------------------


class TestSQLiteProjectMetaStore:
    def test_save_and_get(self) -> None:
        s = SQLiteProjectMetaStore()
        m = StoredProjectMeta(project_path="/proj", name="myproj", language="python")
        s.save(m)
        result = s.get("/proj")
        assert result is not None
        assert result.name == "myproj"
        s.close()

    def test_get_not_found(self) -> None:
        s = SQLiteProjectMetaStore()
        assert s.get("/missing") is None
        s.close()

    def test_list_all(self) -> None:
        s = SQLiteProjectMetaStore()
        s.save(StoredProjectMeta(project_path="/a"))
        s.save(StoredProjectMeta(project_path="/b"))
        assert len(s.list_all()) == 2
        s.close()

    def test_delete(self) -> None:
        s = SQLiteProjectMetaStore()
        s.save(StoredProjectMeta(project_path="/proj"))
        assert s.delete("/proj") is True
        assert s.get("/proj") is None
        s.close()

    def test_metadata_roundtrip(self) -> None:
        s = SQLiteProjectMetaStore()
        m = StoredProjectMeta(
            project_path="/proj",
            name="p",
            metadata={"tags": ["web", "api"]},
        )
        s.save(m)
        result = s.get("/proj")
        assert result.metadata == {"tags": ["web", "api"]}
        s.close()
