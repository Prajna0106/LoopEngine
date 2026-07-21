"""Tests for GradleValidator."""

from __future__ import annotations

from loopengine.adapters.outbound.validation.gradle_validator import GradleValidator


class TestGradleValidator:
    def test_name(self) -> None:
        v = GradleValidator()
        assert v.name == "gradle"

    def test_command(self) -> None:
        v = GradleValidator()
        assert v.command == ["gradle"]

    def test_build_args_default(self) -> None:
        v = GradleValidator()
        args = v.build_args([])
        assert args == ["gradle", "check", "--no-daemon", "--console=plain"]

    def test_build_args_custom_task(self) -> None:
        v = GradleValidator()
        args = v.build_args([], config={"task": "build"})
        assert "build" in args

    def test_build_args_extra_args(self) -> None:
        v = GradleValidator()
        args = v.build_args([], config={"extra_args": ["--info"]})
        assert "--info" in args

    def test_parse_build_success(self) -> None:
        v = GradleValidator()
        stdout = "BUILD SUCCESSFUL in 2s"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert issues == []

    def test_parse_build_failed(self) -> None:
        v = GradleValidator()
        stdout = "BUILD FAILED\nFAILURE: Build failed with an exception."
        passed, _issues = v.parse_output(stdout, "", 1)
        assert passed is False

    def test_parse_task_failure(self) -> None:
        v = GradleValidator()
        stdout = "> Task :compileJava FAILED"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) == 1
        assert issues[0].rule == "task_failure"

    def test_parse_java_compilation_error(self) -> None:
        v = GradleValidator()
        stdout = "/src/Main.java:10: error: cannot find symbol"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].file == "/src/Main.java"
        assert issues[0].line == 10

    def test_parse_kotlin_compilation_error(self) -> None:
        v = GradleValidator()
        stdout = "e: /src/Main.kt:5:1 Unresolved reference: foo"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].file == "/src/Main.kt"
        assert issues[0].line == 5

    def test_parse_test_failure(self) -> None:
        v = GradleValidator()
        stdout = "> Task :test FAILED"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert any(i.rule == "test_failure" for i in issues)

    def test_parse_empty_output(self) -> None:
        v = GradleValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []
