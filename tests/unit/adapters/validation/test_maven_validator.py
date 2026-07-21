"""Tests for MavenValidator."""

from __future__ import annotations

from loopengine.adapters.outbound.validation.maven_validator import MavenValidator
from loopengine.core.ports.outbound.validator_port import Severity


class TestMavenValidator:
    def test_name(self) -> None:
        v = MavenValidator()
        assert v.name == "maven"

    def test_command(self) -> None:
        v = MavenValidator()
        assert v.command == ["mvn"]

    def test_build_args_default(self) -> None:
        v = MavenValidator()
        args = v.build_args([])
        assert args == ["mvn", "validate", "--batch-mode", "--fail-at-end"]

    def test_build_args_custom_goal(self) -> None:
        v = MavenValidator()
        args = v.build_args([], config={"goal": "compile"})
        assert "compile" in args

    def test_build_args_with_profiles(self) -> None:
        v = MavenValidator()
        args = v.build_args([], config={"profiles": ["prod", "fast"]})
        assert "-P" in args
        assert "prod,fast" in args

    def test_build_args_with_properties(self) -> None:
        v = MavenValidator()
        args = v.build_args([], config={"properties": {"skipTests": "true"}})
        assert "-DskipTests=true" in args

    def test_parse_build_success(self) -> None:
        v = MavenValidator()
        stdout = "[INFO] BUILD SUCCESS\n[INFO] Total time: 1.234s"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert issues == []

    def test_parse_build_failure(self) -> None:
        v = MavenValidator()
        stdout = "[ERROR] BUILD FAILURE\n[ERROR] Compilation failure"
        passed, _issues = v.parse_output(stdout, "", 1)
        assert passed is False

    def test_parse_compilation_error(self) -> None:
        v = MavenValidator()
        stdout = "[ERROR] /src/Main.java:[10,5] cannot find symbol"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) == 1
        assert issues[0].file == "/src/Main.java"
        assert issues[0].line == 10
        assert issues[0].column == 5
        assert issues[0].severity == Severity.ERROR

    def test_parse_test_failure(self) -> None:
        v = MavenValidator()
        stdout = (
            "[ERROR] Tests run: 10, Failures: 2, Errors: 1, Skipped: 0,"
            " Time elapsed: 1.5s [ERROR] SomeTest Time elapsed: 0.1s"
        )
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert any(i.rule == "test_failure" for i in issues)

    def test_parse_generic_error(self) -> None:
        v = MavenValidator()
        stdout = "[ERROR] Could not resolve dependencies"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) >= 1

    def test_parse_empty_output(self) -> None:
        v = MavenValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []
