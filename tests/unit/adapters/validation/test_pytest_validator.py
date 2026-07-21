"""Tests for PytestValidator."""

from __future__ import annotations

from loopengine.adapters.outbound.validation.pytest_validator import PytestValidator
from loopengine.core.ports.outbound.validator_port import Severity


class TestPytestValidator:
    def test_name(self) -> None:
        v = PytestValidator()
        assert v.name == "pytest"

    def test_command(self) -> None:
        v = PytestValidator()
        assert v.command == ["pytest"]

    def test_build_args_default(self) -> None:
        v = PytestValidator()
        args = v.build_args(["tests/"])
        assert args == ["pytest", "--tb=short", "--no-header", "-q", "tests/"]

    def test_build_args_empty_paths(self) -> None:
        v = PytestValidator()
        args = v.build_args([])
        assert args == ["pytest", "--tb=short", "--no-header", "-q"]

    def test_build_args_with_markers(self) -> None:
        v = PytestValidator()
        args = v.build_args([], config={"markers": "slow"})
        assert "-m" in args
        assert "slow" in args

    def test_parse_all_pass(self) -> None:
        v = PytestValidator()
        stdout = "5 passed in 0.12s"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert issues == []

    def test_parse_some_fail(self) -> None:
        v = PytestValidator()
        stdout = (
            "3 passed, 2 failed in 0.5s\n"
            "FAILED tests/test_a.py::test_one - assert 1 == 2\n"
            "FAILED tests/test_b.py::test_two - ValueError"
        )
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) == 2
        assert issues[0].severity == Severity.ERROR
        assert issues[0].rule == "test_failure"

    def test_parse_errors(self) -> None:
        v = PytestValidator()
        stdout = "1 passed, 1 error in 0.3s\nERROR tests/test_c.py::test_broken - ImportError"
        passed, issues = v.parse_output(stdout, "", 2)
        assert passed is False
        assert any(i.rule == "test_error" for i in issues)

    def test_parse_warnings(self) -> None:
        v = PytestValidator()
        stdout = "1 passed in 0.1s\nWARNING deprecation notice"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert any(i.rule == "warning" for i in issues)
        assert any(i.severity == Severity.WARNING for i in issues)

    def test_parse_mixed_results(self) -> None:
        v = PytestValidator()
        stdout = (
            "4 passed, 1 failed, 1 error in 1.0s\n"
            "FAILED tests/test_x.py::test_fail - AssertionError\n"
            "ERROR tests/test_y.py::test_err - RuntimeError"
        )
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) >= 2

    def test_parse_empty_output(self) -> None:
        v = PytestValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []

    def test_parse_no_tests_collected(self) -> None:
        v = PytestValidator()
        stdout = "no tests ran"
        passed, _issues = v.parse_output(stdout, "", 5)
        assert passed is False
