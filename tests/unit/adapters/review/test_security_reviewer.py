"""Tests for SecurityReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.security_reviewer import SecurityReviewer


class TestSecurityReviewer:
    def test_name(self) -> None:
        r = SecurityReviewer()
        assert r.name == "security"

    def test_clean_code(self) -> None:
        r = SecurityReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        assert result.score == 10.0

    def test_hardcoded_secret(self) -> None:
        r = SecurityReviewer()
        content = 'password = "supersecret123"'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "config.py", "content": content}],
        )
        assert result.score < 10.0
        issues = result.metadata["issues"]
        assert any(i["rule"] == "hardcoded_secret" for i in issues)
        assert any(i["severity"] == "critical" for i in issues)

    def test_sql_injection(self) -> None:
        r = SecurityReviewer()
        content = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "db.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "sql_injection" for i in issues)

    def test_eval_exec(self) -> None:
        r = SecurityReviewer()
        content = "result = eval(user_input)"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "eval_exec" for i in issues)

    def test_insecure_random(self) -> None:
        r = SecurityReviewer()
        content = "token = random.randint(0, 1000000)"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "token.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "insecure_random" for i in issues)

    def test_hardcoded_host(self) -> None:
        r = SecurityReviewer()
        content = 'host = "192.168.1.100"'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "config.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "hardcoded_host" for i in issues)

    def test_recommendations(self) -> None:
        r = SecurityReviewer()
        content = 'password = "secret"'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "config.py", "content": content}],
        )
        assert len(result.metadata["recommendations"]) > 0
