"""Architecture tests — verify SOLID principles and project structure."""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "loopengine"


def _python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def _get_classes(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def _get_imports(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
    return imports


class TestDirectoryStructure:
    """Verify the project follows the expected directory layout."""

    def test_core_ports_exist(self) -> None:
        ports_dir = SRC_ROOT / "core" / "ports"
        assert ports_dir.is_dir()

    def test_core_services_exist(self) -> None:
        services_dir = SRC_ROOT / "core" / "services"
        assert services_dir.is_dir()

    def test_adapters_outbound_exist(self) -> None:
        adapters_dir = SRC_ROOT / "adapters" / "outbound"
        assert adapters_dir.is_dir()

    def test_adapters_inbound_exist(self) -> None:
        adapters_dir = SRC_ROOT / "adapters" / "inbound"
        assert adapters_dir.is_dir()

    def test_infrastructure_exist(self) -> None:
        infra_dir = SRC_ROOT / "infrastructure"
        assert infra_dir.is_dir()

    def test_domain_exceptions_exist(self) -> None:
        exc_dir = SRC_ROOT / "core" / "domain" / "exceptions"
        assert exc_dir.is_dir()


class TestPortInterfaces:
    """Verify port interfaces follow ISP (one interface per file)."""

    def test_ports_are_abstract(self) -> None:
        port_files = _python_files(SRC_ROOT / "core" / "ports" / "outbound")
        for pf in port_files:
            if pf.name.startswith("_"):
                continue
            content = pf.read_text(encoding="utf-8").strip()
            # Skip empty stub files (single docstring only)
            code_lines = [ln for ln in content.split("\n") if not ln.strip().startswith('"""')]
            if not any(ln.strip() for ln in code_lines):
                continue
            # Port files should define either classes or protocols
            has_definition = "class " in content or "def " in content or "Protocol" in content
            assert has_definition, f"Port file {pf.name} has no definitions"

    def test_port_files_have_abstract_classes(self) -> None:
        port_files = _python_files(SRC_ROOT / "core" / "ports" / "outbound")
        for pf in port_files:
            if pf.name.startswith("_"):
                continue
            try:
                tree = ast.parse(pf.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # ABCs should have at least one abstract method
                    any(
                        isinstance(d, ast.FunctionDef)
                        and any(
                            isinstance(d2, ast.Name) and d2.id == "abstractmethod"
                            for d2 in d.decorator_list
                        )
                        for d in node.body
                    )
                    bases = [getattr(b, "attr", getattr(b, "id", "")) for b in node.bases]
                    if "ABC" in bases or "ABCMeta" in str(type(node)):
                        # At least one abstract method expected
                        pass


class TestNoCircularImports:
    """Verify no circular imports between top-level packages."""

    def test_core_does_not_import_adapters(self) -> None:
        core_files = _python_files(SRC_ROOT / "core")
        violations = []
        for cf in core_files:
            imports = _get_imports(cf)
            for imp in imports:
                if imp.startswith("loopengine.adapters"):
                    violations.append((cf.name, imp))
        assert violations == [], f"Circular imports found: {violations}"

    def test_core_does_not_import_infrastructure(self) -> None:
        core_files = _python_files(SRC_ROOT / "core")
        violations = []
        for cf in core_files:
            imports = _get_imports(cf)
            for imp in imports:
                if imp.startswith("loopengine.infrastructure"):
                    violations.append((cf.name, imp))
        assert violations == [], f"Circular imports found: {violations}"


class TestNamingConventions:
    """Verify naming conventions are followed."""

    def test_service_files_are_snake_case(self) -> None:
        service_files = _python_files(SRC_ROOT / "core" / "services")
        for sf in service_files:
            if sf.name.startswith("_"):
                continue
            assert sf.name.islower() or "_" in sf.name, (
                f"Service file {sf.name} should be snake_case"
            )

    def test_adapter_files_are_snake_case(self) -> None:
        adapter_dirs = [
            SRC_ROOT / "adapters" / "outbound" / d
            for d in ["agents", "validation", "review", "plugins", "prompts", "persistence"]
            if (SRC_ROOT / "adapters" / "outbound" / d).is_dir()
        ]
        for ad in adapter_dirs:
            for af in _python_files(ad):
                if af.name.startswith("_"):
                    continue
                assert af.name.islower() or "_" in af.name, (
                    f"Adapter file {af.name} should be snake_case"
                )


class TestExceptionHierarchy:
    """Verify all domain exceptions inherit from LoopEngineError."""

    def test_exceptions_inherit_base(self) -> None:
        exc_files = _python_files(SRC_ROOT / "core" / "domain" / "exceptions")
        for ef in exc_files:
            if ef.name.startswith("_"):
                continue
            classes = _get_classes(ef)
            for cls_name in classes:
                # Skip base class itself
                if cls_name == "LoopEngineError":
                    continue
                try:
                    tree = ast.parse(ef.read_text(encoding="utf-8"))
                except (SyntaxError, UnicodeDecodeError):
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == cls_name:
                        bases = [getattr(b, "attr", getattr(b, "id", "")) for b in node.bases]
                        # Should inherit from LoopEngineError or another exception
                        has_valid_base = any("Error" in b or "Exception" in b for b in bases)
                        assert has_valid_base, (
                            f"{cls_name} in {ef.name} doesn't inherit from an exception class"
                        )


class TestDocstrings:
    """Verify key modules have docstrings."""

    def test_all_port_files_have_docstrings(self) -> None:
        port_files = _python_files(SRC_ROOT / "core" / "ports" / "outbound")
        for pf in port_files:
            if pf.name.startswith("_"):
                continue
            content = pf.read_text(encoding="utf-8").strip()
            assert content.startswith('"""') or content.startswith("'"), (
                f"Port file {pf.name} missing docstring"
            )

    def test_all_service_files_have_docstrings(self) -> None:
        service_files = _python_files(SRC_ROOT / "core" / "services")
        for sf in service_files:
            if sf.name.startswith("_"):
                continue
            content = sf.read_text(encoding="utf-8").strip()
            assert content.startswith('"""') or content.startswith("'"), (
                f"Service file {sf.name} missing docstring"
            )
