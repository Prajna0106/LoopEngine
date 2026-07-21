"""Tests for NPMValidator."""

from __future__ import annotations

from loopengine.adapters.outbound.validation.npm_validator import NPMValidator
from loopengine.core.ports.outbound.validator_port import Severity


class TestNPMValidator:
    def test_name(self) -> None:
        v = NPMValidator()
        assert v.name == "npm"

    def test_command(self) -> None:
        v = NPMValidator()
        assert v.command == ["npm"]

    def test_build_args_default(self) -> None:
        v = NPMValidator()
        args = v.build_args([])
        assert args == ["npm", "run", "test", "--"]

    def test_build_args_custom_script(self) -> None:
        v = NPMValidator()
        args = v.build_args([], config={"script": "lint"})
        assert "lint" in args

    def test_parse_no_errors(self) -> None:
        v = NPMValidator()
        stdout = "0 errors, 0 warnings"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert issues == []

    def test_parse_eslint_errors(self) -> None:
        v = NPMValidator()
        stdout = "3 errors and 2 warnings"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) >= 1
        assert issues[0].severity == Severity.ERROR

    def test_parse_eslint_warnings_only(self) -> None:
        v = NPMValidator()
        stdout = "0 errors and 5 warnings"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert any(i.severity == Severity.WARNING for i in issues)

    def test_parse_individual_eslint_results(self) -> None:
        v = NPMValidator()
        stdout = "  10:1  error  Unexpected any  @typescript-eslint/no-explicit-any"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert len(issues) == 1
        assert issues[0].line == 10
        assert issues[0].column == 1
        assert issues[0].severity == Severity.ERROR

    def test_parse_typescript_error(self) -> None:
        v = NPMValidator()
        stdout = "error TS2345: Argument of type 'string' is not assignable"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].rule == "TS2345"

    def test_parse_jest_failure(self) -> None:
        v = NPMValidator()
        stdout = "FAIL tests/app.test.ts"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].rule == "test_failure"
        assert issues[0].file == "tests/app.test.ts"

    def test_parse_empty_output(self) -> None:
        v = NPMValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []
