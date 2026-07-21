"""Tests for APIDesignReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.api_design_reviewer import APIDesignReviewer


class TestAPIDesignReviewer:
    def test_name(self) -> None:
        r = APIDesignReviewer()
        assert r.name == "api_design"

    def test_clean_code(self) -> None:
        r = APIDesignReviewer()
        content = '"""Module."""\ndef my_func() -> int:\n    return 1'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        assert result.score == 10.0

    def test_mutable_default(self) -> None:
        r = APIDesignReviewer()
        content = "def func(items=[]):\n    pass"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "mutable_default" for i in issues)

    def test_bare_except(self) -> None:
        r = APIDesignReviewer()
        content = "try:\n    pass\nexcept:\n    pass"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "bare_except" for i in issues)

    def test_mixed_naming(self) -> None:
        r = APIDesignReviewer()
        content = "def snake_case():\n    pass\ndef camelCase():\n    pass"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "mixed_naming" for i in issues)

    def test_missing_return_type(self) -> None:
        r = APIDesignReviewer()
        content = "def public_func():\n    return 1"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "missing_return_type" for i in issues)
