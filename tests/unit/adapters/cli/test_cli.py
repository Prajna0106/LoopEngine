"""CLI tests using Typer's CliRunner."""

from __future__ import annotations

from typer.testing import CliRunner

from loopengine.adapters.inbound.cli.app import app

runner = CliRunner()


class TestCLIHelp:
    def test_help_flag(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "LoopEngine" in result.output

    def test_no_args_shows_help(self) -> None:
        result = runner.invoke(app, [])
        # Typer returns exit code 2 when no subcommand is given with no_args_is_help
        assert result.exit_code in (0, 2)

    def test_json_flag(self) -> None:
        result = runner.invoke(app, ["--json", "--help"])
        assert result.exit_code == 0


class TestCLIInitCommand:
    def test_init_help(self) -> None:
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialise" in result.output or "init" in result.output.lower()


class TestCLIDoctorCommand:
    def test_doctor_help(self) -> None:
        result = runner.invoke(app, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "health" in result.output.lower() or "doctor" in result.output.lower()


class TestCLIPlanCommand:
    def test_plan_help(self) -> None:
        result = runner.invoke(app, ["plan", "--help"])
        assert result.exit_code == 0
        assert "plan" in result.output.lower()


class TestCLIRunCommand:
    def test_run_help(self) -> None:
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output.lower()


class TestCLIReviewCommand:
    def test_review_help(self) -> None:
        result = runner.invoke(app, ["review", "--help"])
        assert result.exit_code == 0
        assert "review" in result.output.lower()


class TestCLIImproveCommand:
    def test_improve_help(self) -> None:
        result = runner.invoke(app, ["improve", "--help"])
        assert result.exit_code == 0
        assert "improve" in result.output.lower()


class TestCLILoggingOptions:
    def test_verbose_flag(self) -> None:
        result = runner.invoke(app, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_log_level_option(self) -> None:
        result = runner.invoke(app, ["--log-level", "DEBUG", "--help"])
        assert result.exit_code == 0
