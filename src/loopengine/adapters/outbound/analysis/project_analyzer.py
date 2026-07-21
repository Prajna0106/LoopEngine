"""Project analyzer — detect language, frameworks, tools, and metadata.

Scans a project directory to produce a structured ``ProjectInfo`` summary
that downstream components (planner, executor, validators) can consume.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# ── Data model ─────────────────────────────────────────────────────────


class ProjectInfo(BaseModel):
    """Structured metadata about a project directory."""

    # Identity
    name: str = Field(default="", description="Project name")
    version: str = Field(default="", description="Project version")
    description: str = Field(default="", description="Project description")

    # Language & runtime
    languages: list[str] = Field(
        default_factory=list,
        description="Detected programming languages",
    )
    python_version: str = Field(default="", description="Python version constraint")

    # Frameworks
    frameworks: list[str] = Field(
        default_factory=list,
        description="Detected frameworks (django, fastapi, react, ...)",
    )

    # Package management
    package_manager: str = Field(default="", description="Primary package manager")
    lock_files: list[str] = Field(
        default_factory=list,
        description="Detected lock files",
    )

    # Testing
    test_framework: str = Field(default="", description="Primary test framework")
    test_paths: list[str] = Field(
        default_factory=list,
        description="Detected test directories",
    )

    # Infrastructure
    has_docker: bool = Field(default=False, description="Docker files present")
    docker_files: list[str] = Field(
        default_factory=list,
        description="Docker-related file paths",
    )
    has_ci: bool = Field(default=False, description="CI/CD config present")
    ci_systems: list[str] = Field(
        default_factory=list,
        description="Detected CI systems (github_actions, gitlab_ci, ...)",
    )

    # Tooling
    linters: list[str] = Field(default_factory=list, description="Detected linters")
    formatters: list[str] = Field(default_factory=list, description="Detected formatters")
    type_checkers: list[str] = Field(
        default_factory=list,
        description="Detected type checkers",
    )

    # Raw file inventory (top-level)
    root_files: list[str] = Field(
        default_factory=list,
        description="Top-level files in the project root",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Extra detection results",
    )


# ── Detection helpers ──────────────────────────────────────────────────

# Extension → language (order matters for overlap)
_EXT_LANG: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".pyx": "python",
    ".rs": "rust",
    ".go": "go",
    ".go.mod": "go",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".kt": "kotlin",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".c": "c",
    ".h": "c",
    ".swift": "swift",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
}

# Dependency name → framework
_FW_DEPS: dict[str, str] = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    "starlette": "starlette",
    "uvicorn": "uvicorn",
    "celery": "celery",
    "tornado": "tornado",
    "bottle": "bottle",
    "sanic": "sanic",
    "react": "react",
    "vue": "vue",
    "svelte": "svelte",
    "next": "nextjs",
    "nuxt": "nuxt",
    "angular": "angular",
    "express": "express",
    "fastify": "fastify",
    "nestjs": "nestjs",
    "rails": "rails",
    "sinatra": "sinatra",
    "laravel": "laravel",
    "spring-boot": "spring",
    "quarkus": "quarkus",
    "rust-axum": "axum",
    "axum": "axum",
    "actix-web": "actix",
    "gin": "gin",
    "echo": "echo",
    "fiber": "fiber",
}

# Dependency name → test framework
_TEST_FW: dict[str, str] = {
    "pytest": "pytest",
    "unittest2": "unittest",
    "nose2": "nose",
    "nose": "nose",
    "jest": "jest",
    "vitest": "vitest",
    "mocha": "mocha",
    "jasmine": "jasmine",
    "karma": "karma",
    "cypress": "cypress",
    "playwright": "playwright",
    "rspec": "rspec",
    "minitest": "minitest",
    "junit": "junit",
    "testng": "testng",
    "cargo-test": "cargo_test",
    "go-test": "go_test",
}

# Dependency name → linter
_LINTER_DEPS: dict[str, str] = {
    "ruff": "ruff",
    "flake8": "flake8",
    "pylint": "pylint",
    "eslint": "eslint",
    "biome": "biome",
    "golangci-lint": "golangci_lint",
    "clippy": "clippy",
    "rubocop": "rubocop",
    "phpstan": "phpstan",
}

# Dependency name → formatter
_FORMATTER_DEPS: dict[str, str] = {
    "black": "black",
    "ruff": "ruff",
    "isort": "isort",
    "prettier": "prettier",
    "biome": "biome",
    "rustfmt": "rustfmt",
    "gofmt": "gofmt",
    "ktlint": "ktlint",
}

# Dependency name → type checker
_TYPECHECKER_DEPS: dict[str, str] = {
    "mypy": "mypy",
    "pyright": "pyright",
    "pytype": "pytype",
    "typescript": "typescript",
    "mypy-extensions": "mypy",
}

# CI config files
_CI_DETECT: dict[str, str] = {
    ".github/workflows": "github_actions",
    ".gitlab-ci.yml": "gitlab_ci",
    ".gitlab-ci.yaml": "gitlab_ci",
    "Jenkinsfile": "jenkins",
    ".circleci/config.yml": "circleci",
    ".circleci/config.yaml": "circleci",
    ".travis.yml": "travis",
    "azure-pipelines.yml": "azure_pipelines",
    "azure-pipelines.yaml": "azure_pipelines",
    "bitbucket-pipelines.yml": "bitbucket_pipelines",
    "bitbucket-pipelines.yaml": "bitbucket_pipelines",
    ".buildkite": "buildkite",
}

# Docker files
_DOCKER_FILES = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "docker-compose.dev.yml",
    "docker-compose.dev.yaml",
    "docker-compose.prod.yml",
    "docker-compose.prod.yaml",
    ".dockerignore",
}

# Package managers — lock files
_PM_DETECT: dict[str, str] = {
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "package-lock.json": "npm",
    "bun.lockb": "bun",
    "Gemfile.lock": "bundler",
    "Cargo.lock": "cargo",
    "go.sum": "go",
    "composer.lock": "composer",
    "pubspec.lock": "dart",
    "mix.lock": "mix",
}

# Files that indicate a package manager (manifests)
_PM_MANIFEST: dict[str, str] = {
    "pyproject.toml": "uv",
    "Pipfile": "pipenv",
    "Cargo.toml": "cargo",
    "go.mod": "go",
    "package.json": "npm",
    "Gemfile": "bundler",
    "composer.json": "composer",
    "pubspec.yaml": "dart",
    "mix.exs": "mix",
}

# Hidden directories to allow during walk (CI config lives here)
_HIDDEN_DIRS_ALLOW: set[str] = {
    ".github",
    ".circleci",
    ".buildkite",
    ".gitlab",
}


# ── Analyzer ───────────────────────────────────────────────────────────


class ProjectAnalyzer:
    """Scans a project directory and returns a ``ProjectInfo`` summary.

    Usage::

        analyzer = ProjectAnalyzer()
        info = analyzer.analyze("/path/to/project")
        print(info.languages)
    """

    def __init__(self, *, max_depth: int = 3, max_files: int = 500) -> None:
        self._max_depth = max_depth
        self._max_files = max_files

    def analyze(self, project_path: str | Path) -> ProjectInfo:
        """Analyze *project_path* and return structured metadata."""
        root = Path(project_path).resolve()
        if not root.is_dir():
            return ProjectInfo(name=root.name)

        root_files = self._list_root_files(root)
        all_files = self._collect_files(root)
        extensions = self._extensions(all_files)

        languages = self._detect_languages(extensions, all_files, root)
        frameworks = self._detect_frameworks(root)
        package_manager = self._detect_package_manager(root, all_files)
        lock_files = self._detect_lock_files(all_files)
        test_framework, test_paths = self._detect_testing(root, all_files)
        has_docker, docker_files = self._detect_docker(all_files, root)
        has_ci, ci_systems = self._detect_ci(all_files, root)
        linters = self._detect_linters(root)
        formatters = self._detect_formatters(root)
        type_checkers = self._detect_type_checkers(root)
        name, version, description, python_version = self._extract_identity(root)

        return ProjectInfo(
            name=name,
            version=version,
            description=description,
            languages=languages,
            python_version=python_version,
            frameworks=frameworks,
            package_manager=package_manager,
            lock_files=lock_files,
            test_framework=test_framework,
            test_paths=test_paths,
            has_docker=has_docker,
            docker_files=docker_files,
            has_ci=has_ci,
            ci_systems=ci_systems,
            linters=linters,
            formatters=formatters,
            type_checkers=type_checkers,
            root_files=root_files,
        )

    # ── File collection ───────────────────────────────────────────────

    def _list_root_files(self, root: Path) -> list[str]:
        try:
            return sorted(p.name for p in root.iterdir() if not p.name.startswith("."))
        except PermissionError:
            return []

    def _list_hidden_root_files(self, root: Path) -> list[str]:
        """List hidden files/dirs at the root level (for CI/docker detection)."""
        try:
            return sorted(p.name for p in root.iterdir() if p.name.startswith("."))
        except PermissionError:
            return []

    def _collect_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        _walk(root, root, files, self._max_depth, self._max_files)
        return files

    def _extensions(self, files: list[Path]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for f in files:
            ext = f.suffix.lower()
            if ext:
                counts[ext] = counts.get(ext, 0) + 1
        return counts

    # ── Language detection ────────────────────────────────────────────

    def _detect_languages(
        self,
        extensions: dict[str, int],
        files: list[Path],
        root: Path,
    ) -> list[str]:
        langs: set[str] = set()

        for ext in extensions:
            if ext in _EXT_LANG:
                langs.add(_EXT_LANG[ext])

        # Check manifest files by filename
        for f in files:
            if f.name == "go.mod":
                langs.add("go")
            elif f.name == "Cargo.toml":
                langs.add("rust")
            elif f.name == "Gemfile":
                langs.add("ruby")
            elif f.name == "composer.json":
                langs.add("php")
            elif f.name == "pubspec.yaml":
                langs.add("dart")
            elif f.name == "mix.exs":
                langs.add("elixir")

        # Infer Python from pyproject.toml (if no .py files exist yet)
        if "python" not in langs and (root / "pyproject.toml").exists():
            text = (root / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
            if _is_python_pyproject(text):
                langs.add("python")

        return sorted(langs)

    # ── Framework detection ───────────────────────────────────────────

    def _detect_frameworks(self, root: Path) -> list[str]:
        deps = self._all_dep_names(root)
        return sorted({v for k, v in _FW_DEPS.items() if k in deps})

    # ── Package manager detection ─────────────────────────────────────

    def _detect_package_manager(self, root: Path, files: list[Path]) -> str:
        # Prefer lock files
        for f in files:
            if f.name in _PM_DETECT:
                return _PM_DETECT[f.name]

        # Fall back to manifest files
        for name, pm in _PM_MANIFEST.items():
            if (root / name).exists():
                return pm

        return ""

    def _detect_lock_files(self, files: list[Path]) -> list[str]:
        return sorted(f.name for f in files if f.name in _PM_DETECT)

    # ── Testing detection ─────────────────────────────────────────────

    def _detect_testing(self, root: Path, _files: list[Path]) -> tuple[str, list[str]]:
        deps = self._all_dep_names(root)
        test_fw = ""
        for dep, fw in _TEST_FW.items():
            if dep in deps:
                test_fw = fw
                break

        # Config-file based detection
        test_paths: list[str] = []
        if not test_fw:
            for cfg in ("pytest.ini", "setup.cfg", "tox.ini", "conftest.py"):
                if (root / cfg).exists():
                    test_fw = "pytest"
                    break

            # Check pyproject.toml for [tool.pytest.ini_options]
            if not test_fw:
                pyproject = root / "pyproject.toml"
                if pyproject.exists():
                    text = pyproject.read_text(encoding="utf-8", errors="replace")
                    if "[tool.pytest" in text:
                        test_fw = "pytest"

            if (root / "jest.config.js").exists() or (root / "jest.config.ts").exists():
                test_fw = "jest"
            if (root / "vitest.config.ts").exists() or (root / "vitest.config.js").exists():
                test_fw = "vitest"
            if (root / ".mocharc.yml").exists() or (root / ".mocharc.yaml").exists():
                test_fw = "mocha"

        # Detect test directories
        for dirname in ("tests", "test", "__tests__", "spec", "specs"):
            if (root / dirname).is_dir():
                test_paths.append(dirname)

        return test_fw, test_paths

    # ── Docker detection ──────────────────────────────────────────────

    def _detect_docker(self, files: list[Path], root: Path) -> tuple[bool, list[str]]:
        found: set[str] = set()
        for f in files:
            if f.name in _DOCKER_FILES:
                found.add(f.name)
        # Also check root for hidden files like .dockerignore
        for name in (".dockerignore",):
            if (root / name).exists():
                found.add(name)
        return bool(found), sorted(found)

    # ── CI detection ──────────────────────────────────────────────────

    def _detect_ci(self, files: list[Path], root: Path) -> tuple[bool, list[str]]:
        systems: set[str] = set()
        for f in files:
            rel = f.as_posix()
            for pattern, system in _CI_DETECT.items():
                if pattern in rel:
                    systems.add(system)

        # Also check root-level CI files (hidden, not collected by _walk)
        for name, system in _CI_DETECT.items():
            # Only check root-level files (not directories like .github/workflows)
            if "/" not in name and (root / name).exists():
                systems.add(system)

        # Check .github/workflows directory at root
        workflows = root / ".github" / "workflows"
        if workflows.is_dir():
            systems.add("github_actions")

        # Check .circleci at root
        circleci = root / ".circleci"
        if circleci.is_dir():
            systems.add("circleci")

        return bool(systems), sorted(systems)

    # ── Tooling detection ─────────────────────────────────────────────

    def _detect_linters(self, root: Path) -> list[str]:
        deps = self._all_dep_names(root)
        found = sorted({v for k, v in _LINTER_DEPS.items() if k in deps})

        # Config file detection
        if (root / ".flake8").exists() and "flake8" not in found:
            found.append("flake8")
        has_eslint = (root / ".eslintrc").exists() or (root / ".eslintrc.js").exists()
        if has_eslint and "eslint" not in found:
            found.append("eslint")

        return found

    def _detect_formatters(self, root: Path) -> list[str]:
        deps = self._all_dep_names(root)
        return sorted({v for k, v in _FORMATTER_DEPS.items() if k in deps})

    def _detect_type_checkers(self, root: Path) -> list[str]:
        deps = self._all_dep_names(root)
        found = sorted({v for k, v in _TYPECHECKER_DEPS.items() if k in deps})

        if (root / "tsconfig.json").exists() and "typescript" not in found:
            found.append("typescript")

        return found

    # ── Identity extraction ───────────────────────────────────────────

    def _extract_identity(self, root: Path) -> tuple[str, str, str, str]:
        name = root.name
        version = ""
        description = ""
        python_version = ""

        # pyproject.toml
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            n, v, d = _parse_pyproject_meta(text)
            if n:
                name = n
            if v:
                version = v
            if d:
                description = d
            python_version = _parse_pyproject_python(text)

        # package.json (fills gaps)
        pkg = root / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8", errors="replace")
            n, v, d = _parse_package_json_meta(text)
            if n:
                name = n
            if v:
                version = v
            if d:
                description = d

        # Cargo.toml (fills gaps)
        cargo = root / "Cargo.toml"
        if cargo.exists():
            text = cargo.read_text(encoding="utf-8", errors="replace")
            n, v = _parse_cargo_meta(text)
            if n:
                name = n
            if v:
                version = v

        return name, version, description, python_version

    # ── Dependency name extraction ────────────────────────────────────

    def _all_dep_names(self, root: Path) -> set[str]:
        names: set[str] = set()

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            names.update(_extract_pyproject_deps(text))

        pkg = root / "package.json"
        if pkg.exists():
            text = pkg.read_text(encoding="utf-8", errors="replace")
            names.update(_extract_package_json_deps(text))

        requirements = root / "requirements.txt"
        if requirements.exists():
            text = requirements.read_text(encoding="utf-8", errors="replace")
            names.update(_extract_requirements_deps(text))

        cargo = root / "Cargo.toml"
        if cargo.exists():
            text = cargo.read_text(encoding="utf-8", errors="replace")
            names.update(_extract_cargo_deps(text))

        gemfile = root / "Gemfile"
        if gemfile.exists():
            text = gemfile.read_text(encoding="utf-8", errors="replace")
            names.update(_extract_gemfile_deps(text))

        return names


# ── File-system walker ─────────────────────────────────────────────────


def _walk(
    root: Path,
    current: Path,
    files: list[Path],
    max_depth: int,
    max_files: int,
) -> None:
    if len(files) >= max_files:
        return
    depth = len(current.relative_to(root).parts)
    if depth > max_depth:
        return
    try:
        for entry in sorted(current.iterdir()):
            if len(files) >= max_files:
                return
            # Skip hidden dirs/files, except known CI directories
            if entry.name.startswith(".") and entry.is_dir():
                if entry.name in _HIDDEN_DIRS_ALLOW:
                    _walk(root, entry, files, max_depth, max_files)
                continue
            if entry.name.startswith("."):
                continue
            if entry.is_file():
                files.append(entry)
            elif entry.is_dir():
                _walk(root, entry, files, max_depth, max_files)
    except PermissionError:
        pass


# ── Tiny parsers (no external deps) ───────────────────────────────────


def _parse_pyproject_meta(text: str) -> tuple[str, str, str]:
    name = version = description = ""
    in_project = False
    for line in text.splitlines():
        s = line.strip()
        if s == "[project]":
            in_project = True
            continue
        if s.startswith("[") and in_project:
            in_project = False
            continue
        if in_project:
            if s.startswith("name"):
                name = _extract_quoted(s)
            elif s.startswith("version"):
                version = _extract_quoted(s)
            elif s.startswith("description"):
                description = _extract_quoted(s)
    return name, version, description


def _parse_pyproject_python(text: str) -> str:
    in_project = False
    for line in text.splitlines():
        s = line.strip()
        if s == "[project]":
            in_project = True
            continue
        if s.startswith("[") and in_project:
            break
        if in_project and s.startswith("requires-python"):
            return _extract_quoted(s).strip("\"'")
    return ""


def _parse_package_json_meta(text: str) -> tuple[str, str, str]:
    name = version = description = ""
    for line in text.splitlines():
        s = line.strip().rstrip(",")
        # Handle single-line JSON: {"name": "foo", "version": "1.0"}
        if s.startswith("{"):
            s = s[1:].strip()
        if s.startswith("}"):
            s = s[:-1].strip()
        # Split single-line into individual key-value segments
        segments = _split_json_segments(s)
        for raw_seg in segments:
            seg = raw_seg.strip().rstrip(",")
            if seg.startswith('"name"'):
                name = _extract_json_val(seg)
            elif seg.startswith('"version"'):
                version = _extract_json_val(seg)
            elif seg.startswith('"description"'):
                description = _extract_json_val(seg)
    return name, version, description


def _split_json_segments(s: str) -> list[str]:
    """Split a JSON object body into individual ``"key": value`` segments.

    Handles quoted strings that may contain commas.
    """
    segments: list[str] = []
    current: list[str] = []
    in_quote = False
    for ch in s:
        if ch == '"':
            in_quote = not in_quote
            current.append(ch)
        elif ch == "," and not in_quote:
            segments.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        remaining = "".join(current).strip()
        if remaining:
            segments.append(remaining)
    return segments


def _parse_cargo_meta(text: str) -> tuple[str, str]:
    name = version = ""
    in_package = False
    for line in text.splitlines():
        s = line.strip()
        if s == "[package]":
            in_package = True
            continue
        if s.startswith("["):
            in_package = False
            continue
        if in_package:
            if s.startswith("name"):
                name = _extract_quoted(s)
            elif s.startswith("version"):
                version = _extract_quoted(s)
    return name, version


def _extract_pyproject_deps(text: str) -> set[str]:
    """Extract dependency names from pyproject.toml.

    Handles two formats:
    1. PEP 621 inline list: ``dependencies = ["fastapi", "uvicorn"]``
    2. PEP 621 multi-line list::

        dependencies = [
            "fastapi>=0.100",
            "uvicorn",
        ]

    3. Section-based: ``[project.dependencies]`` (rare)
    """
    deps: set[str] = set()
    in_project = False
    in_deps_section = False
    in_optional_section = False
    in_deps_list = False  # tracking multi-line list

    for line in text.splitlines():
        s = line.strip()

        # Track [project] section
        if s == "[project]":
            in_project = True
            in_deps_section = False
            in_optional_section = False
            in_deps_list = False
            continue

        # Track [project.dependencies] section (rare)
        if s == "[project.dependencies]":
            in_deps_section = True
            in_optional_section = False
            in_project = False
            in_deps_list = False
            continue

        # Track [project.optional-dependencies.*] sections
        if s.startswith("[project.optional-dependencies"):
            in_optional_section = True
            in_deps_section = False
            in_project = False
            in_deps_list = False
            continue

        # Any other section header resets state
        if s.startswith("[") and not s.startswith("[tool."):
            in_project = False
            in_deps_section = False
            in_optional_section = False
            in_deps_list = False
            continue

        # Inside [project] section: parse inline list
        if in_project and not in_deps_list and s.startswith("dependencies"):
            result = _parse_inline_toml_list(s)
            if result:
                deps.update(result)
            elif "[" in s and "]" not in s:
                # Multi-line list starts: dependencies = [
                in_deps_list = True
            continue

        # Continue collecting multi-line list items
        if in_deps_list:
            if "]" in s:
                # End of multi-line list - check if there's a trailing item
                before_bracket = s.split("]")[0].strip().rstrip(",")
                if before_bracket:
                    dep = _strip_version_specifier(before_bracket.strip('"').strip("'"))
                    if dep:
                        deps.add(dep)
                in_deps_list = False
            else:
                # List item line
                item = s.strip().rstrip(",")
                if item:
                    dep = _strip_version_specifier(item.strip('"').strip("'"))
                    if dep:
                        deps.add(dep)
            continue

        # Inside [project.dependencies] or [project.optional-dependencies.*] sections
        if in_deps_section or in_optional_section:
            # Inline list format: dev = ["pytest", "ruff"]
            if "=" in s and "[" in s:
                deps.update(_parse_inline_toml_list(s.split("=", 1)[1]))
                continue
            # Bare quoted strings (rare section-based format)
            if s.startswith('"') or s.startswith("'"):
                dep = _parse_dep_name(s)
                if dep:
                    deps.add(dep)

    return deps


def _parse_inline_toml_list(line: str) -> set[str]:
    """Parse ``dependencies = ["dep1", "dep2"]`` or multi-line start."""
    deps: set[str] = set()
    # Find content between [ and ]
    start = line.find("[")
    end = line.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return deps
    content = line[start + 1 : end]
    for item in content.split(","):
        dep = item.strip().strip('"').strip("'")
        if dep:
            # Strip version specifiers
            dep = _strip_version_specifier(dep)
            if dep:
                deps.add(dep)
    return deps


def _strip_version_specifier(name: str) -> str:
    """Strip version specifiers from a package name.

    ``"django>=4.0"`` → ``"django"``
    ``"fastapi[all]"`` → ``"fastapi"``
    """
    for op in (">=", "<=", "==", "!=", ">", "<", "~=", "[", ";"):
        idx = name.find(op)
        if idx != -1:
            name = name[:idx]
    return name.strip().lower()


def _parse_dep_name(s: str) -> str:
    """Extract package name from a dependency string like ``"fastapi>=0.100"``."""
    dep = s.strip().strip('"').strip("'")
    # Strip version specifiers
    for op in (">=", "<=", "==", "!=", ">", "<", "~=", "["):
        idx = dep.find(op)
        if idx != -1:
            dep = dep[:idx]
    return dep.strip().lower()


def _extract_package_json_deps(text: str) -> set[str]:
    deps: set[str] = set()
    in_deps = False

    for line in text.splitlines():
        s = line.strip().rstrip(",")

        # Match "dependencies": {, "devDependencies": {, etc.
        # Handle both multi-line and single-line formats.
        for key in ('"dependencies"', '"devDependencies"', '"peerDependencies"'):
            if key in s and ":" in s:
                # Check if deps are on the same line (single-line JSON)
                after_colon = s.split(key, 1)[1]
                if "{" in after_colon:
                    # Single-line: extract the inner object
                    deps.update(_extract_inner_json_deps(after_colon))
                    in_deps = True
                else:
                    # Multi-line: deps start on next lines
                    in_deps = True
                break

        if s == "}" and in_deps:
            in_deps = False
            continue

        if in_deps and s.startswith('"'):
            dep = s.split('"')[1]
            if dep:
                deps.add(dep.lower())

    return deps


def _extract_inner_json_deps(text: str) -> set[str]:
    """Extract package names from the inner deps object.

    ``": {"react": "^18.0", "vue": "^3.0"}}`` → ``{"react", "vue"}``
    """
    deps: set[str] = set()
    # Find the inner { after "dependencies":
    idx = text.find("{")
    if idx == -1:
        return deps
    content = text[idx + 1 :]
    # Remove everything after the matching }
    depth = 1
    end = 0
    for i, ch in enumerate(content):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    content = content[:end]
    if not content:
        return deps
    # Split on commas and extract quoted keys
    for raw_item in content.split(","):
        item = raw_item.strip()
        if item.startswith('"'):
            key = item.split('"')[1]
            if key:
                deps.add(key.lower())
    return deps


def _extract_requirements_deps(text: str) -> set[str]:
    deps: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("-"):
            continue
        dep = s.split("=")[0].split(">")[0].split("<")[0].split("!")[0].split("[")[0].strip()
        if dep:
            deps.add(dep.lower())
    return deps


def _extract_cargo_deps(text: str) -> set[str]:
    deps: set[str] = set()
    in_deps = False
    for line in text.splitlines():
        s = line.strip()
        if s == "[dependencies]":
            in_deps = True
            continue
        if s.startswith("["):
            in_deps = False
            continue
        if in_deps and s and not s.startswith("#"):
            dep = s.split("=")[0].split(">")[0].split("<")[0].strip()
            if dep:
                deps.add(dep.lower())
    return deps


def _extract_gemfile_deps(text: str) -> set[str]:
    deps: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("gem ") or s.startswith('gem "'):
            parts = s.split('"')
            if len(parts) >= 2:
                deps.add(parts[1].lower())
    return deps


# ── Tiny value extractors ──────────────────────────────────────────────


def _extract_quoted(line: str) -> str:
    for ch in ('"', "'"):
        if ch in line:
            parts = line.split(ch, 2)
            if len(parts) >= 3:
                return parts[1]
    return ""


def _extract_json_val(line: str) -> str:
    """Extract value from a JSON key-value pair like ``"key": "value"``."""
    parts = line.split(":", 1)
    if len(parts) < 2:
        return ""
    val = parts[1].strip()
    # Remove trailing commas, braces, and whitespace
    val = val.rstrip(",").rstrip("}").rstrip()
    # Strip quotes
    val = val.strip('"').strip("'")
    return val


def _is_python_pyproject(text: str) -> bool:
    """Return True if pyproject.toml looks like a Python project."""
    indicators = (
        "[project]",
        "dependencies",
        "requires-python",
        "build-system",
        "[tool.pytest",
        "[tool.mypy",
        "[tool.ruff",
        "[tool.black",
        "[project.scripts",
        "poetry",
    )
    return any(ind in text for ind in indicators)
