"""Tests for PerformanceReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.performance_reviewer import PerformanceReviewer


class TestPerformanceReviewer:
    def test_name(self) -> None:
        r = PerformanceReviewer()
        assert r.name == "performance"

    def test_clean_code(self) -> None:
        r = PerformanceReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        assert result.score == 10.0

    def test_n_plus_one(self) -> None:
        r = PerformanceReviewer()
        content = "for user in User.objects.all():\n    print(user.posts.all())"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "views.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "n_plus_one" for i in issues)

    def test_string_concat_loop(self) -> None:
        r = PerformanceReviewer()
        content = "result = ''\nfor i in range(100):\n    result += str(i)"
        r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )

    def test_blocking_sleep(self) -> None:
        r = PerformanceReviewer()
        content = "async def handler():\n    time.sleep(1)"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "async.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "blocking_sleep" for i in issues)
