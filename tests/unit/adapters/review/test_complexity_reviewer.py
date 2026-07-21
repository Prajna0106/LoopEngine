"""Tests for ComplexityReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.complexity_reviewer import ComplexityReviewer


class TestComplexityReviewer:
    def test_name(self) -> None:
        r = ComplexityReviewer()
        assert r.name == "complexity"

    def test_clean_code(self) -> None:
        r = ComplexityReviewer()
        content = "def foo():\n    return 1"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        assert result.score == 10.0

    def test_long_function(self) -> None:
        r = ComplexityReviewer()
        lines = ["def long_func():"] + ["    x = 1"] * 60
        content = "\n".join(lines)
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "long_function" for i in issues)

    def test_deep_nesting(self) -> None:
        r = ComplexityReviewer()
        content = (
            "def deep():\n"
            "    if True:\n"
            "        if True:\n"
            "            if True:\n"
            "                if True:\n"
            "                    if True:\n"
            "                        x = 1"
        )
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "deep_nesting" for i in issues)

    def test_too_many_params(self) -> None:
        r = ComplexityReviewer()
        content = "def func(a, b, c, d, e, f, g):\n    pass"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "too_many_params" for i in issues)
