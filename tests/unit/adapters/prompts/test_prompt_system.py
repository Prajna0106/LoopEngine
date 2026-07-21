"""Tests for InMemoryPromptRegistry and FilePromptProvider."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from loopengine.adapters.outbound.prompts.file_prompt_provider import (
    FilePromptProvider,
)
from loopengine.adapters.outbound.prompts.prompt_registry import (
    InMemoryPromptRegistry,
)
from loopengine.core.domain.exceptions.prompt_exceptions import (
    PromptNotFoundError,
    PromptValidationError,
)
from loopengine.core.ports.outbound.prompt_port import (
    PromptTemplate,
    PromptVersion,
)


class TestPromptTemplate:
    def test_defaults(self) -> None:
        t = PromptTemplate(name="p", content="hello")
        assert t.name == "p"
        assert t.version == "1.0.0"
        assert t.variables == []
        assert t.tags == []

    def test_custom(self) -> None:
        t = PromptTemplate(
            name="p",
            content="hi {name}",
            version="2.0.0",
            variables=["name"],
            tags=["greeting"],
            description="A greeting",
        )
        assert t.version == "2.0.0"
        assert t.variables == ["name"]
        assert "greeting" in t.tags


class TestPromptVersion:
    def test_creation(self) -> None:
        v = PromptVersion(version="1.0.0", content="hello", changelog="initial")
        assert v.version == "1.0.0"
        assert v.changelog == "initial"


class TestInMemoryPromptRegistry:
    def test_register_and_get(self) -> None:
        reg = InMemoryPromptRegistry()
        t = PromptTemplate(name="greet", content="Hello!")
        reg.register(t)
        assert reg.get("greet").content == "Hello!"

    def test_get_latest(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="v1", version="1.0.0"))
        reg.register(PromptTemplate(name="p", content="v2", version="2.0.0"))
        assert reg.get("p").content == "v2"

    def test_get_specific_version(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="v1", version="1.0.0"))
        reg.register(PromptTemplate(name="p", content="v2", version="2.0.0"))
        assert reg.get("p", "1.0.0").content == "v1"

    def test_get_not_found(self) -> None:
        reg = InMemoryPromptRegistry()
        with pytest.raises(PromptNotFoundError):
            reg.get("nonexistent")

    def test_get_version_not_found(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="v1", version="1.0.0"))
        with pytest.raises(PromptNotFoundError):
            reg.get("p", "9.0.0")

    def test_list_prompts_empty(self) -> None:
        reg = InMemoryPromptRegistry()
        assert reg.list_prompts() == []

    def test_list_prompts(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="a", content="a"))
        reg.register(PromptTemplate(name="b", content="b"))
        assert len(reg.list_prompts()) == 2

    def test_list_prompts_by_tag(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="a", content="a", tags=["x"]))
        reg.register(PromptTemplate(name="b", content="b", tags=["y"]))
        reg.register(PromptTemplate(name="c", content="c", tags=["x", "y"]))
        x_prompts = reg.list_prompts(tag="x")
        assert len(x_prompts) == 2

    def test_list_versions(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="v1", version="1.0.0"))
        reg.register(PromptTemplate(name="p", content="v2", version="2.0.0"))
        versions = reg.list_versions("p")
        assert len(versions) == 2
        assert versions[0].version == "1.0.0"
        assert versions[1].version == "2.0.0"

    def test_list_versions_not_found(self) -> None:
        reg = InMemoryPromptRegistry()
        with pytest.raises(PromptNotFoundError):
            reg.list_versions("nonexistent")

    def test_render_simple(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="Hello {name}!"))
        result = reg.render("p", {"name": "World"})
        assert result == "Hello World!"

    def test_render_multiple_variables(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{a} and {b}"))
        result = reg.render("p", {"a": "X", "b": "Y"})
        assert result == "X and Y"

    def test_render_missing_variable(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x} {y}", variables=["x", "y"]))
        with pytest.raises(PromptValidationError):
            reg.render("p", {"x": "1"})

    def test_render_no_variables(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="No vars here"))
        result = reg.render("p")
        assert result == "No vars here"

    def test_render_caching(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        r1 = reg.render("p", {"x": "1"})
        r2 = reg.render("p", {"x": "1"})
        assert r1 == r2 == "1"

    def test_render_different_variables_no_cache_hit(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        r1 = reg.render("p", {"x": "a"})
        r2 = reg.render("p", {"x": "b"})
        assert r1 == "a"
        assert r2 == "b"

    def test_invalidate_cache_all(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        reg.render("p", {"x": "1"})
        reg.invalidate_cache()
        assert reg._cache == {}

    def test_invalidate_cache_by_name(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        reg.render("p", {"x": "1"})
        assert len(reg._cache) == 1
        reg.invalidate_cache("p")
        assert len(reg._cache) == 0

    def test_invalidate_cache_other_name(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        reg.register(PromptTemplate(name="q", content="{y}"))
        reg.render("p", {"x": "1"})
        reg.render("q", {"y": "2"})
        reg.invalidate_cache("p")
        assert len(reg._cache) == 1

    def test_register_overwrites_same_version(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="old", version="1.0.0"))
        reg.register(PromptTemplate(name="p", content="new", version="1.0.0"))
        assert reg.get("p").content == "new"

    def test_register_invalidates_cache(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="{x}"))
        reg.render("p", {"x": "1"})
        assert len(reg._cache) == 1
        reg.register(PromptTemplate(name="p", content="{x} v2"))
        assert len(reg._cache) == 0

    def test_render_not_found(self) -> None:
        reg = InMemoryPromptRegistry()
        with pytest.raises(PromptNotFoundError):
            reg.render("nonexistent")

    def test_list_versions_returns_sorted(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="v3", version="3.0.0"))
        reg.register(PromptTemplate(name="p", content="v1", version="1.0.0"))
        reg.register(PromptTemplate(name="p", content="v2", version="2.0.0"))
        versions = reg.list_versions("p")
        assert [v.version for v in versions] == ["1.0.0", "2.0.0", "3.0.0"]

    def test_render_integer_variable(self) -> None:
        reg = InMemoryPromptRegistry()
        reg.register(PromptTemplate(name="p", content="Count: {n}"))
        result = reg.render("p", {"n": 42})
        assert result == "Count: 42"


class TestFilePromptProvider:
    def test_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = FilePromptProvider(tmpdir)
            assert p.name == "filesystem"

    def test_load_all_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = FilePromptProvider(tmpdir)
            assert p.load_all() == []

    def test_load_all_nonexistent_dir(self) -> None:
        p = FilePromptProvider("/nonexistent/path")
        assert p.load_all() == []

    def test_load_all_simple_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "greet.md").write_text("Hello {name}!")
            p = FilePromptProvider(tmpdir)
            templates = p.load_all()
            assert len(templates) == 1
            assert templates[0].name == "greet"
            assert templates[0].content == "Hello {name}!"
            assert templates[0].variables == ["name"]

    def test_load_all_with_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = (
                '---\nversion: "2.0.0"\nvariables: [goal]'
                "\ntags: [planning]\ndescription: Plan prompt"
                "\n---\nPlan: {goal}"
            )
            Path(tmpdir, "plan.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            templates = p.load_all()
            assert len(templates) == 1
            t = templates[0]
            assert t.version == "2.0.0"
            assert t.variables == ["goal"]
            assert "planning" in t.tags
            assert t.description == "Plan prompt"
            assert t.content == "Plan: {goal}"

    def test_load_all_inline_list_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = '---\nversion: "1.0.0"\nvariables: [a, b, c]\n---\n{a} {b} {c}'
            Path(tmpdir, "multi.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            templates = p.load_all()
            assert templates[0].variables == ["a", "b", "c"]

    def test_load_all_skips_empty_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "empty.md").write_text("")
            p = FilePromptProvider(tmpdir)
            assert p.load_all() == []

    def test_load_all_skips_whitespace_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "blank.md").write_text("   \n  \n  ")
            p = FilePromptProvider(tmpdir)
            assert p.load_all() == []

    def test_load_specific(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.md").write_text("Prompt A")
            Path(tmpdir, "b.md").write_text("Prompt B")
            p = FilePromptProvider(tmpdir)
            t = p.load("a")
            assert t is not None
            assert t.content == "Prompt A"

    def test_load_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = FilePromptProvider(tmpdir)
            assert p.load("nonexistent") is None

    def test_load_all_auto_detects_variables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "p.md").write_text("{x} and {y} and {x} again")
            p = FilePromptProvider(tmpdir)
            templates = p.load_all()
            assert templates[0].variables == ["x", "y"]

    def test_load_all_string_front_matter_value(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = '---\nversion: "1.0.0"\n---\nHello'
            Path(tmpdir, "p.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            t = p.load("p")
            assert t is not None
            assert t.version == "1.0.0"

    def test_load_all_boolean_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "---\ndraft: true\n---\nHello"
            Path(tmpdir, "p.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            t = p.load("p")
            assert t is not None

    def test_load_all_integer_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "---\npriority: 5\n---\nHello"
            Path(tmpdir, "p.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            t = p.load("p")
            assert t is not None

    def test_load_all_list_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            content = "---\ntags:\n- alpha\n- beta\n---\nHello"
            Path(tmpdir, "p.md").write_text(content)
            p = FilePromptProvider(tmpdir)
            t = p.load("p")
            assert t is not None
            assert t.tags == ["alpha", "beta"]
