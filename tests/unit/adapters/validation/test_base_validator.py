"""Tests for BaseValidator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from loopengine.adapters.outbound.validation.base_validator import (
    BaseValidator,
    ValidatorConfig,
)
from loopengine.core.ports.outbound.validator_port import Severity


class ConcreteValidator(BaseValidator):
    """Minimal concrete validator for testing."""

    @property
    def name(self) -> str:
        return "test-tool"

    @property
    def command(self) -> list[str]:
        return ["test-tool", "check"]


class TestValidatorConfig:
    def test_defaults(self) -> None:
        cfg = ValidatorConfig()
        assert cfg.timeout == 120.0
        assert cfg.cwd is None
        assert cfg.env == {}

    def test_custom(self) -> None:
        cfg = ValidatorConfig(timeout=30.0, cwd="/home/user", env={"FOO": "bar"})
        assert cfg.timeout == 30.0
        assert cfg.cwd == "/home/user"
        assert cfg.env == {"FOO": "bar"}


class TestBaseValidator:
    def test_name_and_command(self) -> None:
        v = ConcreteValidator()
        assert v.name == "test-tool"
        assert v.command == ["test-tool", "check"]

    def test_build_args_default(self) -> None:
        v = ConcreteValidator()
        args = v.build_args(["src/"], config=None)
        assert args == ["test-tool", "check", "src/"]

    def test_build_args_empty_paths(self) -> None:
        v = ConcreteValidator()
        args = v.build_args([], config=None)
        assert args == ["test-tool", "check"]

    def test_is_available_false_when_missing(self) -> None:
        v = ConcreteValidator()
        with patch("shutil.which", return_value=None):
            assert v.is_available() is False

    def test_is_available_true_when_found(self) -> None:
        v = ConcreteValidator()
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            assert v.is_available() is True

    def test_validate_returns_error_when_not_available(self) -> None:
        v = ConcreteValidator()
        with patch("shutil.which", return_value=None):
            result = v.validate(["src/"])
        assert result.passed is False
        assert len(result.issues) == 1
        assert "not installed" in result.issues[0].message

    @patch("loopengine.adapters.outbound.validation.base_validator.subprocess.run")
    def test_validate_success(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n", stderr="")
        v = ConcreteValidator()
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            result = v.validate(["src/"])
        assert result.passed is True
        assert result.issues == []
        assert result.duration_ms >= 0

    @patch("loopengine.adapters.outbound.validation.base_validator.subprocess.run")
    def test_validate_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error: something broke")
        v = ConcreteValidator()
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            result = v.validate(["src/"])
        assert result.passed is False
        assert len(result.issues) == 1
        assert result.issues[0].severity == Severity.ERROR

    @patch("loopengine.adapters.outbound.validation.base_validator.subprocess.run")
    def test_validate_timeout(self, mock_run: MagicMock) -> None:
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test-tool", timeout=5.0)
        v = ConcreteValidator(config=ValidatorConfig(timeout=5.0))
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            result = v.validate(["src/"])
        assert result.passed is False
        assert "timed out" in result.issues[0].message

    @patch("loopengine.adapters.outbound.validation.base_validator.subprocess.run")
    def test_validate_file_not_found(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError
        v = ConcreteValidator()
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            result = v.validate(["src/"])
        assert result.passed is False
        assert "CLI not found" in result.issues[0].message

    @patch("loopengine.adapters.outbound.validation.base_validator.subprocess.run")
    def test_validate_os_error(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = OSError("permission denied")
        v = ConcreteValidator()
        with patch("shutil.which", return_value="/usr/bin/test-tool"):
            result = v.validate(["src/"])
        assert result.passed is False
        assert "Failed to execute" in result.issues[0].message
