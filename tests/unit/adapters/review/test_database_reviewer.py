"""Tests for DatabaseReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.database_reviewer import DatabaseReviewer


class TestDatabaseReviewer:
    def test_name(self) -> None:
        r = DatabaseReviewer()
        assert r.name == "database"

    def test_clean_code(self) -> None:
        r = DatabaseReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        assert result.score == 10.0

    def test_sql_interpolation(self) -> None:
        r = DatabaseReviewer()
        content = 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "db.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "sql_interpolation" for i in issues)
        assert any(i["severity"] == "critical" for i in issues)

    def test_select_star(self) -> None:
        r = DatabaseReviewer()
        content = 'cursor.execute("SELECT * FROM users")'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "db.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "select_star" for i in issues)

    def test_n_plus_one(self) -> None:
        r = DatabaseReviewer()
        content = "for user in User.objects.all():\n    print(user)"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "views.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "n_plus_one" for i in issues)

    def test_no_transaction(self) -> None:
        r = DatabaseReviewer()
        content = "user = User.objects.create(name='test')"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "views.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "no_transaction" for i in issues)
