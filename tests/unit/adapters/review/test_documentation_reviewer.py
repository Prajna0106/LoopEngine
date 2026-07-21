"""Tests for DocumentationReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.documentation_reviewer import DocumentationReviewer


class TestDocumentationReviewer:
    def test_name(self) -> None:
        r = DocumentationReviewer()
        assert r.name == "documentation"

    def test_clean_code(self) -> None:
        r = DocumentationReviewer()
        content = '"""Module docstring."""\ndef foo():\n    """Do something."""\n    pass'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = [i for i in result.metadata["issues"] if i["rule"] == "missing_func_doc"]
        assert len(issues) == 0

    def test_missing_module_doc(self) -> None:
        r = DocumentationReviewer()
        content = "def foo(): pass"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "missing_module_doc" for i in issues)

    def test_missing_func_doc(self) -> None:
        r = DocumentationReviewer()
        content = '"""Module."""\ndef public_func():\n    pass'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "missing_func_doc" for i in issues)

    def test_todo_without_ticket(self) -> None:
        r = DocumentationReviewer()
        content = '"""Module."""\n# TODO: fix this'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "todo_no_ticket" for i in issues)

    def test_todo_with_ticket(self) -> None:
        r = DocumentationReviewer()
        content = '"""Module."""\n# TODO [PROJ-123]: fix this'
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert not any(i["rule"] == "todo_no_ticket" for i in issues)

    def test_skips_non_python(self) -> None:
        r = DocumentationReviewer()
        content = "# just a comment"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "readme.md", "content": content}],
        )
        assert result.score == 10.0
