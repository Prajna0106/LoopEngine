"""Tests for ScalabilityReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.scalability_reviewer import ScalabilityReviewer


class TestScalabilityReviewer:
    def test_name(self) -> None:
        r = ScalabilityReviewer()
        assert r.name == "scalability"

    def test_clean_code(self) -> None:
        r = ScalabilityReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        assert result.score == 10.0

    def test_full_file_read(self) -> None:
        r = ScalabilityReviewer()
        content = "data = open('big.txt').readlines()"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "full_file_read" for i in issues)

    def test_nested_iteration(self) -> None:
        r = ScalabilityReviewer()
        content = "for k, v in data.items():\n    for item in other:\n        pass"
        r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
