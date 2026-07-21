"""Tests for PythonValidator."""

from __future__ import annotations

import json

from loopengine.adapters.outbound.validation.python_validator import PythonValidator
from loopengine.core.ports.outbound.validator_port import Severity


class TestPythonValidator:
    def test_name(self) -> None:
        v = PythonValidator()
        assert v.name == "python"

    def test_command(self) -> None:
        v = PythonValidator()
        assert v.command == ["ruff", "check"]

    def test_build_args_default(self) -> None:
        v = PythonValidator()
        args = v.build_args(["src/"])
        assert args == ["ruff", "check", "--output-format=json", "src/"]

    def test_build_args_with_config_select(self) -> None:
        v = PythonValidator()
        args = v.build_args(["src/"], config={"select": ["E", "F"]})
        assert "--select" in args
        assert "E,F" in args

    def test_build_args_with_config_ignore(self) -> None:
        v = PythonValidator()
        args = v.build_args(["src/"], config={"ignore": ["E501"]})
        assert "--ignore" in args
        assert "E501" in args

    def test_parse_output_no_violations(self) -> None:
        v = PythonValidator()
        passed, issues = v.parse_output("[]", "", 0)
        assert passed is True
        assert issues == []

    def test_parse_output_with_violations(self) -> None:
        v = PythonValidator()
        data = [
            {
                "code": "E501",
                "message": "line too long",
                "filename": "src/main.py",
                "location": {"row": 10, "column": 1},
            }
        ]
        passed, issues = v.parse_output(json.dumps(data), "", 1)
        assert passed is False
        assert len(issues) == 1
        assert issues[0].message == "line too long"
        assert issues[0].file == "src/main.py"
        assert issues[0].line == 10
        assert issues[0].column == 1
        assert issues[0].rule == "E501"
        assert issues[0].severity == Severity.WARNING

    def test_parse_output_undefined_name_is_error(self) -> None:
        v = PythonValidator()
        data = [
            {
                "code": "F821",
                "message": "undefined name 'x'",
                "filename": "src/main.py",
                "location": {"row": 5, "column": 1},
            }
        ]
        _, issues = v.parse_output(json.dumps(data), "", 1)
        assert issues[0].severity == Severity.ERROR

    def test_parse_output_syntax_error(self) -> None:
        v = PythonValidator()
        data = [
            {
                "code": "E999",
                "message": "SyntaxError: invalid syntax",
                "filename": "src/main.py",
                "location": {"row": 1, "column": 1},
            }
        ]
        _, issues = v.parse_output(json.dumps(data), "", 1)
        assert issues[0].severity == Severity.ERROR

    def test_parse_output_empty_stdout_zero_exit(self) -> None:
        v = PythonValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []

    def test_parse_output_empty_stdout_nonzero_exit(self) -> None:
        v = PythonValidator()
        passed, issues = v.parse_output("", "some error", 1)
        assert passed is False
        assert len(issues) == 1

    def test_parse_output_text_fallback(self) -> None:
        v = PythonValidator()
        text = "src/main.py:10:1: E501 line too long (90 > 79)"
        passed, issues = v.parse_output(text, "", 1)
        assert passed is False
        assert len(issues) == 1
        assert issues[0].file == "src/main.py"
        assert issues[0].line == 10
