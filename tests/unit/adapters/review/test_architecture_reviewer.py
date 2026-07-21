"""Tests for ArchitectureReviewer."""

from __future__ import annotations

from loopengine.adapters.outbound.review.architecture_reviewer import ArchitectureReviewer


class TestArchitectureReviewer:
    def test_name(self) -> None:
        r = ArchitectureReviewer()
        assert r.name == "architecture"

    def test_clean_code(self) -> None:
        r = ArchitectureReviewer()
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "main.py", "content": "x = 1"}],
        )
        assert result.score == 10.0

    def test_god_class(self) -> None:
        r = ArchitectureReviewer()
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(25)])
        content = f"class Big:\n{methods}"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "big.py", "content": content}],
        )
        assert result.score < 10.0
        assert any(c.message for c in result.comments)
        assert result.metadata["reviewer"] == "architecture"

    def test_god_class_rule(self) -> None:
        r = ArchitectureReviewer()
        methods = "\n".join([f"    def method_{i}(self): pass" for i in range(25)])
        content = f"class Big:\n{methods}"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "big.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "god_class" for i in issues)

    def test_circular_import(self) -> None:
        r = ArchitectureReviewer()
        content = "from pkg.module import Foo\nfrom pkg.module import Bar"
        result = r.review(
            goal="test",
            artifacts=[{"kind": "file", "path": "pkg/module.py", "content": content}],
        )
        issues = result.metadata["issues"]
        assert any(i["rule"] == "circular_import" for i in issues)
