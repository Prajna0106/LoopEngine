"""SQLite persistence adapter.

Provides SQLite-backed implementations of all memory store repositories.
Uses standard library sqlite3 — no external dependencies.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

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

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv_store (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS executions (
    workflow_id  TEXT PRIMARY KEY,
    goal         TEXT NOT NULL,
    status       TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    completed_at TEXT DEFAULT '',
    iterations   INTEGER DEFAULT 0,
    summary      TEXT DEFAULT '',
    metadata     TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS reflections (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id   TEXT NOT NULL,
    iteration      INTEGER NOT NULL,
    decision       TEXT NOT NULL,
    issues_count   INTEGER DEFAULT 0,
    suggestions_count INTEGER DEFAULT 0,
    summary        TEXT DEFAULT '',
    metadata       TEXT DEFAULT '{}',
    FOREIGN KEY (execution_id) REFERENCES executions(workflow_id)
);
CREATE TABLE IF NOT EXISTS reviews (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id TEXT NOT NULL,
    score        REAL NOT NULL,
    verdict      TEXT NOT NULL,
    issues_count INTEGER DEFAULT 0,
    summary      TEXT DEFAULT '',
    metadata     TEXT DEFAULT '{}',
    FOREIGN KEY (execution_id) REFERENCES executions(workflow_id)
);
CREATE TABLE IF NOT EXISTS project_meta (
    project_path TEXT PRIMARY KEY,
    name         TEXT DEFAULT '',
    language     TEXT DEFAULT '',
    framework    TEXT DEFAULT '',
    metadata     TEXT DEFAULT '{}'
);
"""


class SQLiteMemoryStore(MemoryStore):
    """SQLite-backed key-value store."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def get(self, key: str) -> dict[str, Any] | None:
        row = self._conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        result: dict[str, Any] = json.loads(row["value"])
        return result

    def put(self, key: str, value: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        self._conn.commit()

    def delete(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
        self._conn.commit()
        return cur.rowcount > 0

    def list_keys(self, *, prefix: str = "") -> list[str]:
        if prefix:
            rows = self._conn.execute(
                "SELECT key FROM kv_store WHERE key LIKE ? ORDER BY key",
                (f"{prefix}%",),
            ).fetchall()
        else:
            rows = self._conn.execute("SELECT key FROM kv_store ORDER BY key").fetchall()
        return [row["key"] for row in rows]

    def clear(self) -> int:
        cur = self._conn.execute("DELETE FROM kv_store")
        self._conn.commit()
        return cur.rowcount

    def contains(self, key: str) -> bool:
        row = self._conn.execute("SELECT 1 FROM kv_store WHERE key = ?", (key,)).fetchone()
        return row is not None

    def close(self) -> None:
        self._conn.close()


class SQLiteExecutionHistory(ExecutionHistory):
    """SQLite-backed execution history store."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def save(self, execution: StoredExecution) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO executions
               (workflow_id, goal, status, started_at, completed_at,
                iterations, summary, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                execution.workflow_id,
                execution.goal,
                execution.status,
                execution.started_at,
                execution.completed_at,
                execution.iterations,
                execution.summary,
                json.dumps(execution.metadata),
            ),
        )
        self._conn.commit()

    def get(self, workflow_id: str) -> StoredExecution | None:
        row = self._conn.execute(
            "SELECT * FROM executions WHERE workflow_id = ?", (workflow_id,)
        ).fetchone()
        if row is None:
            return None
        return self._row_to_execution(row)

    def list_all(self) -> list[StoredExecution]:
        rows = self._conn.execute("SELECT * FROM executions ORDER BY started_at").fetchall()
        return [self._row_to_execution(r) for r in rows]

    def delete(self, workflow_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM executions WHERE workflow_id = ?", (workflow_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_execution(row: sqlite3.Row) -> StoredExecution:
        return StoredExecution(
            workflow_id=row["workflow_id"],
            goal=row["goal"],
            status=row["status"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            iterations=row["iterations"],
            summary=row["summary"],
            metadata=json.loads(row["metadata"]),
        )


class SQLiteReflectionStore(ReflectionStore):
    """SQLite-backed reflection store."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def save(self, reflection: StoredReflection) -> None:
        self._conn.execute(
            """INSERT INTO reflections
               (execution_id, iteration, decision, issues_count,
                suggestions_count, summary, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reflection.execution_id,
                reflection.iteration,
                reflection.decision,
                reflection.issues_count,
                reflection.suggestions_count,
                reflection.summary,
                json.dumps(reflection.metadata),
            ),
        )
        self._conn.commit()

    def list_for_execution(self, execution_id: str) -> list[StoredReflection]:
        rows = self._conn.execute(
            "SELECT * FROM reflections WHERE execution_id = ? ORDER BY iteration",
            (execution_id,),
        ).fetchall()
        return [self._row_to_reflection(r) for r in rows]

    def delete(self, execution_id: str) -> int:
        cur = self._conn.execute("DELETE FROM reflections WHERE execution_id = ?", (execution_id,))
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_reflection(row: sqlite3.Row) -> StoredReflection:
        return StoredReflection(
            execution_id=row["execution_id"],
            iteration=row["iteration"],
            decision=row["decision"],
            issues_count=row["issues_count"],
            suggestions_count=row["suggestions_count"],
            summary=row["summary"],
            metadata=json.loads(row["metadata"]),
        )


class SQLiteReviewStore(ReviewStore):
    """SQLite-backed review store."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def save(self, review: StoredReview) -> None:
        self._conn.execute(
            """INSERT INTO reviews
               (execution_id, score, verdict, issues_count, summary, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                review.execution_id,
                review.score,
                review.verdict,
                review.issues_count,
                review.summary,
                json.dumps(review.metadata),
            ),
        )
        self._conn.commit()

    def list_for_execution(self, execution_id: str) -> list[StoredReview]:
        rows = self._conn.execute(
            "SELECT * FROM reviews WHERE execution_id = ?",
            (execution_id,),
        ).fetchall()
        return [self._row_to_review(r) for r in rows]

    def delete(self, execution_id: str) -> int:
        cur = self._conn.execute("DELETE FROM reviews WHERE execution_id = ?", (execution_id,))
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_review(row: sqlite3.Row) -> StoredReview:
        return StoredReview(
            execution_id=row["execution_id"],
            score=row["score"],
            verdict=row["verdict"],
            issues_count=row["issues_count"],
            summary=row["summary"],
            metadata=json.loads(row["metadata"]),
        )


class SQLiteProjectMetaStore(ProjectMetaStore):
    """SQLite-backed project metadata store."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)

    def save(self, meta: StoredProjectMeta) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO project_meta
               (project_path, name, language, framework, metadata)
               VALUES (?, ?, ?, ?, ?)""",
            (
                meta.project_path,
                meta.name,
                meta.language,
                meta.framework,
                json.dumps(meta.metadata),
            ),
        )
        self._conn.commit()

    def get(self, project_path: str) -> StoredProjectMeta | None:
        row = self._conn.execute(
            "SELECT * FROM project_meta WHERE project_path = ?",
            (project_path,),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_meta(row)

    def list_all(self) -> list[StoredProjectMeta]:
        rows = self._conn.execute("SELECT * FROM project_meta ORDER BY project_path").fetchall()
        return [self._row_to_meta(r) for r in rows]

    def delete(self, project_path: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM project_meta WHERE project_path = ?",
            (project_path,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_meta(row: sqlite3.Row) -> StoredProjectMeta:
        return StoredProjectMeta(
            project_path=row["project_path"],
            name=row["name"],
            language=row["language"],
            framework=row["framework"],
            metadata=json.loads(row["metadata"]),
        )
