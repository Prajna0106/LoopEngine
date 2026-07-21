"""Unit tests for ProjectAnalyzer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from loopengine.adapters.outbound.analysis.project_analyzer import ProjectAnalyzer, ProjectInfo


@pytest.fixture()
def analyzer() -> ProjectAnalyzer:
    return ProjectAnalyzer(max_depth=4, max_files=1000)


class TestProjectInfo:
    def test_defaults(self) -> None:
        info = ProjectInfo()
        assert info.name == ""
        assert info.languages == []
        assert not info.has_docker
        assert not info.has_ci

    def test_from_dict(self) -> None:
        info = ProjectInfo(
            name="test",
            languages=["python"],
            frameworks=["fastapi"],
        )
        assert info.name == "test"
        assert "python" in info.languages
        assert "fastapi" in info.frameworks


class TestAnalyzeEmpty:
    def test_empty_dir(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        info = analyzer.analyze(tmp_path)
        assert info.name == tmp_path.name
        assert info.languages == []

    def test_nonexistent_dir(self, analyzer: ProjectAnalyzer) -> None:
        info = analyzer.analyze("/nonexistent/path/xyz")
        assert info.name == "xyz"


class TestLanguageDetection:
    def test_python_project(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("print('hello')")
        (tmp_path / "utils.py").write_text("x = 1")
        info = analyzer.analyze(tmp_path)
        assert "python" in info.languages

    def test_typescript_project(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "index.ts").write_text("console.log('hi')")
        info = analyzer.analyze(tmp_path)
        assert "typescript" in info.languages

    def test_rust_project(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.rs").write_text("fn main() {}")
        info = analyzer.analyze(tmp_path)
        assert "rust" in info.languages

    def test_go_project(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.go").write_text("package main")
        info = analyzer.analyze(tmp_path)
        assert "go" in info.languages

    def test_multi_language(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "api.py").write_text("x = 1")
        (tmp_path / "ui.ts").write_text("const x = 1")
        (tmp_path / "lib.rs").write_text("fn main() {}")
        info = analyzer.analyze(tmp_path)
        assert "python" in info.languages
        assert "typescript" in info.languages
        assert "rust" in info.languages

    def test_python_via_pyproject(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
        info = analyzer.analyze(tmp_path)
        assert "python" in info.languages

    def test_rust_via_cargo(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n")
        info = analyzer.analyze(tmp_path)
        assert "rust" in info.languages

    def test_go_via_gomod(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "go.mod").write_text("module demo\n")
        info = analyzer.analyze(tmp_path)
        assert "go" in info.languages

    def test_ruby_via_gemfile(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Gemfile").write_text('gem "rails"\n')
        info = analyzer.analyze(tmp_path)
        assert "ruby" in info.languages


class TestFrameworkDetection:
    def test_django(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="web"\n\ndependencies = ["django>=4.0"]\n'
        )
        info = analyzer.analyze(tmp_path)
        assert "django" in info.frameworks

    def test_fastapi(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        info = analyzer.analyze(tmp_path)
        assert "fastapi" in info.frameworks

    def test_react(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            '{"dependencies": {"react": "^18.0", "react-dom": "^18.0"}}'
        )
        info = analyzer.analyze(tmp_path)
        assert "react" in info.frameworks

    def test_express(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text('{"dependencies": {"express": "^4.0"}}')
        info = analyzer.analyze(tmp_path)
        assert "express" in info.frameworks

    def test_axum(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text(
            "[package]\nname='web'\n\n[dependencies]\naxum = '0.7'\n"
        )
        info = analyzer.analyze(tmp_path)
        assert "axum" in info.frameworks


class TestPackageManagers:
    def test_uv(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "uv.lock").write_text("")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "uv"
        assert "uv.lock" in info.lock_files

    def test_poetry(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "poetry.lock").write_text("")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "poetry"

    def test_npm(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "package-lock.json").write_text("{}")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "npm"

    def test_pnpm(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pnpm-lock.yaml").write_text("")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "pnpm"

    def test_yarn(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "yarn.lock").write_text("")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "yarn"

    def test_pipenv_fallback(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Pipfile").write_text("")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "pipenv"

    def test_cargo(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text("[package]\nname='demo'\n")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "cargo"

    def test_poetry_preferred_over_pyproject(
        self, analyzer: ProjectAnalyzer, tmp_path: Path
    ) -> None:
        (tmp_path / "poetry.lock").write_text("")
        (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
        info = analyzer.analyze(tmp_path)
        assert info.package_manager == "poetry"


class TestTestingDetection:
    def test_pytest_config(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            "[tool.pytest.ini_options]\ntestpaths=['tests']\n"
        )
        info = analyzer.analyze(tmp_path)
        assert info.test_framework == "pytest"

    def test_pytest_via_dep(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "requirements.txt").write_text("pytest\n")
        info = analyzer.analyze(tmp_path)
        assert info.test_framework == "pytest"

    def test_jest_config(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "jest.config.js").write_text("module.exports = {}")
        info = analyzer.analyze(tmp_path)
        assert info.test_framework == "jest"

    def test_vitest_config(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "vitest.config.ts").write_text("export default {}")
        info = analyzer.analyze(tmp_path)
        assert info.test_framework == "vitest"

    def test_test_dirs(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "tests").mkdir()
        (tmp_path / "test").mkdir()
        info = analyzer.analyze(tmp_path)
        assert "tests" in info.test_paths
        assert "test" in info.test_paths


class TestDockerDetection:
    def test_dockerfile(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
        info = analyzer.analyze(tmp_path)
        assert info.has_docker
        assert "Dockerfile" in info.docker_files

    def test_docker_compose(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "docker-compose.yml").write_text("version: '3'\n")
        (tmp_path / ".dockerignore").write_text("*.pyc\n")
        info = analyzer.analyze(tmp_path)
        assert info.has_docker
        assert len(info.docker_files) == 2

    def test_no_docker(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("")
        info = analyzer.analyze(tmp_path)
        assert not info.has_docker


class TestCIDetection:
    def test_github_actions(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: CI\n")
        info = analyzer.analyze(tmp_path)
        assert info.has_ci
        assert "github_actions" in info.ci_systems

    def test_gitlab_ci(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / ".gitlab-ci.yml").write_text("stages:\n  - test\n")
        info = analyzer.analyze(tmp_path)
        assert info.has_ci
        assert "gitlab_ci" in info.ci_systems

    def test_circleci(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        circle = tmp_path / ".circleci"
        circle.mkdir()
        (circle / "config.yml").write_text("version: 2\n")
        info = analyzer.analyze(tmp_path)
        assert info.has_ci
        assert "circleci" in info.ci_systems

    def test_no_ci(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("")
        info = analyzer.analyze(tmp_path)
        assert not info.has_ci


class TestToolingDetection:
    def test_linters_pyproject(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="x"\n\ndependencies = ["ruff"]\n'
        )
        info = analyzer.analyze(tmp_path)
        assert "ruff" in info.linters

    def test_formatters(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="x"\n\ndependencies = ["black", "isort"]\n'
        )
        info = analyzer.analyze(tmp_path)
        assert "black" in info.formatters
        assert "isort" in info.formatters

    def test_type_checkers(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="x"\n\ndependencies = ["mypy"]\n'
        )
        info = analyzer.analyze(tmp_path)
        assert "mypy" in info.type_checkers

    def test_typescript_via_tsconfig(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "tsconfig.json").write_text("{}")
        info = analyzer.analyze(tmp_path)
        assert "typescript" in info.type_checkers


class TestIdentityExtraction:
    def test_pyproject_identity(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="my-app"\nversion="1.2.3"\ndescription="A cool app"\n'
            'requires-python = ">=3.12"\n'
        )
        info = analyzer.analyze(tmp_path)
        assert info.name == "my-app"
        assert info.version == "1.2.3"
        assert info.description == "A cool app"
        assert info.python_version == ">=3.12"

    def test_package_json_identity(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
            '{"name": "web-app", "version": "0.1.0", "description": "A web app"}'
        )
        info = analyzer.analyze(tmp_path)
        assert info.name == "web-app"
        assert info.version == "0.1.0"

    def test_cargo_identity(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'my-crate'\nversion = '2.0.0'\n")
        info = analyzer.analyze(tmp_path)
        assert info.name == "my-crate"
        assert info.version == "2.0.0"

    def test_fallback_name(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        info = analyzer.analyze(tmp_path)
        assert info.name == tmp_path.name


class TestRootFiles:
    def test_lists_root_files(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_text("")
        (tmp_path / "README.md").write_text("")
        (tmp_path / ".gitignore").write_text("")
        info = analyzer.analyze(tmp_path)
        assert "main.py" in info.root_files
        assert "README.md" in info.root_files
        assert ".gitignore" not in info.root_files  # hidden files excluded


class TestEndToEnd:
    def test_python_fastapi_project(self, analyzer: ProjectAnalyzer, tmp_path: Path) -> None:
        """Simulate a real Python + FastAPI project."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname="fastapi-app"\nversion="0.5.0"\n'
            'description="FastAPI service"\n'
            'requires-python = ">=3.11"\n'
            '\ndependencies = [\n  "fastapi>=0.100",\n  "uvicorn",\n  "pydantic>=2.0",\n]\n'
            '\n[project.optional-dependencies]\ndev = ["pytest", "ruff", "mypy"]\n'
        )
        (tmp_path / "uv.lock").write_text("")
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_main.py").write_text("def test_ok(): ...")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12\n")
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text("name: CI\n")

        info = analyzer.analyze(tmp_path)

        assert info.name == "fastapi-app"
        assert info.version == "0.5.0"
        assert "python" in info.languages
        assert "fastapi" in info.frameworks
        assert info.package_manager == "uv"
        assert "uv.lock" in info.lock_files
        assert info.test_framework == "pytest"
        assert "tests" in info.test_paths
        assert info.has_docker
        assert "Dockerfile" in info.docker_files
        assert info.has_ci
        assert "github_actions" in info.ci_systems
        assert "ruff" in info.linters
        assert "mypy" in info.type_checkers
