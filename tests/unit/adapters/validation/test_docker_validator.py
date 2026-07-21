"""Tests for DockerValidator."""

from __future__ import annotations

from loopengine.adapters.outbound.validation.docker_validator import DockerValidator
from loopengine.core.ports.outbound.validator_port import Severity


class TestDockerValidator:
    def test_name(self) -> None:
        v = DockerValidator()
        assert v.name == "docker"

    def test_command(self) -> None:
        v = DockerValidator()
        assert v.command == ["docker"]

    def test_build_args_default(self) -> None:
        v = DockerValidator()
        args = v.build_args(["Dockerfile"])
        assert args == ["docker", "build", "--no-cache", "-f", "Dockerfile", "."]

    def test_build_args_hadolint_mode(self) -> None:
        v = DockerValidator()
        args = v.build_args(["Dockerfile"], config={"mode": "hadolint"})
        assert args == ["hadolint", "Dockerfile"]

    def test_build_args_with_build_args(self) -> None:
        v = DockerValidator()
        args = v.build_args(
            ["Dockerfile"],
            config={"build_args": {"PYTHON_VERSION": "3.12"}},
        )
        assert "--build-arg" in args
        assert "PYTHON_VERSION=3.12" in args

    def test_parse_build_success(self) -> None:
        v = DockerValidator()
        stdout = "Successfully built abc123"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert issues == []

    def test_parse_hadolint_warning(self) -> None:
        v = DockerValidator()
        stdout = "Dockerfile:3 DL3006 warning: Always tag the version of an image explicitly"
        passed, issues = v.parse_output(stdout, "", 0)
        assert passed is True
        assert len(issues) == 1
        assert issues[0].rule == "DL3006"
        assert issues[0].severity == Severity.WARNING
        assert issues[0].line == 3

    def test_parse_hadolint_error(self) -> None:
        v = DockerValidator()
        stdout = "Dockerfile:1 DL3007 error: Using latest is prone to errors"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].severity == Severity.ERROR

    def test_parse_docker_build_error(self) -> None:
        v = DockerValidator()
        stderr = "error: failed to solve: rpc error: code = Unknown"
        passed, issues = v.parse_output("", stderr, 1)
        assert passed is False
        assert issues[0].rule == "docker_build_error"

    def test_parse_syntax_error(self) -> None:
        v = DockerValidator()
        stdout = "FROM: instruction missing or unknown"
        passed, issues = v.parse_output(stdout, "", 1)
        assert passed is False
        assert issues[0].rule == "syntax_error"

    def test_parse_empty_output(self) -> None:
        v = DockerValidator()
        passed, issues = v.parse_output("", "", 0)
        assert passed is True
        assert issues == []
