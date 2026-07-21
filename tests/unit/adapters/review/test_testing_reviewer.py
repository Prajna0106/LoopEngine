"""Tests for TestingReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.testing_reviewer import TestingReviewer


class TestTestingReviewer:
    def test_name(self) -> None:
        r = TestingReviewer()
        assert r.name == "testing"

    def test_no_tests(self) -> None:
        r = TestingReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "no_tests" for i in issues)
        assert result.score < 10.0

    def test_with_tests(self) -> None:
        r = TestingReviewer()
        result = r.review(
            goal="test",
            artifacts=[
                {"kind": "file", "path": "main.py", "content": "x = 1"},
                {"kind": "file", "path": "test_main.py", "content": "assert True"},
            ],
        )
        issues = result.metadata["issues"]
        assert not any(i["rule"] == "no_tests" for i in issues)

    def test_no_assertions(self) -> None:
        r = TestingReviewer()
        content = "def test_one():\n    pass\ndef test_two():\n    pass"
        result = r.review(
            goal="test",
            artifacts=[
                {"kind": "file", "path": "main.py", "content": "x = 1"},
                {"kind": "file", "path": "test_main.py", "content": content},
            ],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "no_assertions" for i in issues)

    def test_low_test_ratio(self) -> None:
        r = TestingReviewer()
        src_files = [
            {"kind": "file", "path": f"src/file{i}.py", "content": "x = 1"} for i in range(10)
        ]
        test_file = {"kind": "file", "path": "test_one.py", "content": "assert True"}
        result = r.review(goal="test", artifacts=[*src_files, test_file])
        issues = result.metadata["issues"]
        assert any(i["rule"] == "low_test_ratio" for i in issues)
