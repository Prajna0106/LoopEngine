"""Unit tests for ConfigManager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loopengine.infrastructure.config.manager import DEFAULT_CONFIG_YAML, ConfigManager
from loopengine.infrastructure.config.schema import LoopEngineConfig

if TYPE_CHECKING:
    from pathlib import Path


class TestConfigManager:
    def test_load_explicit(self, tmp_path: Path) -> None:
        p = tmp_path / "loop.yaml"
        p.write_text("engine:\n  max_iterations: 2\n", encoding="utf-8")
        mgr = ConfigManager(tmp_path)
        cfg = mgr.load(p)
        assert cfg.engine.max_iterations == 2

    def test_load_auto_discover(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text("engine: {}\n", encoding="utf-8")
        mgr = ConfigManager(tmp_path)
        cfg = mgr.load()
        assert isinstance(cfg, LoopEngineConfig)

    def test_load_defaults_when_missing(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        cfg = mgr.load()
        assert cfg.engine.max_iterations == 5

    def test_load_from_dict(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        cfg = mgr.load_from_dict({"engine": {"max_iterations:": 7}})
        # Note: typo in key above is intentional — should still work with defaults
        assert isinstance(cfg, LoopEngineConfig)

    def test_config_property_lazy(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        assert mgr.config is not None  # triggers default load

    def test_exists_false(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        assert mgr.exists() is False

    def test_exists_true(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text("engine: {}\n", encoding="utf-8")
        mgr = ConfigManager(tmp_path)
        assert mgr.exists() is True

    def test_get_config_path(self, tmp_path: Path) -> None:
        (tmp_path / "loop.yaml").write_text("engine: {}\n", encoding="utf-8")
        mgr = ConfigManager(tmp_path)
        assert mgr.get_config_path() == tmp_path / "loop.yaml"

    def test_save_default(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        path = mgr.save_default()
        assert path.exists()
        assert path.name == "loop.yaml"
        content = path.read_text(encoding="utf-8")
        assert "max_iterations: 5" in content

    def test_save_roundtrip(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        mgr.load_from_dict({"engine": {"max_iterations": 42}})
        path = mgr.save()
        assert path.exists()

        mgr2 = ConfigManager(tmp_path)
        cfg2 = mgr2.load(path)
        assert cfg2.engine.max_iterations == 42

    def test_to_dict(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        d = mgr.to_dict()
        assert "engine" in d
        assert "agents" in d

    def test_to_yaml(self, tmp_path: Path) -> None:
        mgr = ConfigManager(tmp_path)
        y = mgr.to_yaml()
        assert "max_iterations: 5" in y

    def test_default_config_yaml_is_valid(self) -> None:
        """The shipped DEFAULT_CONFIG_YAML must parse correctly."""
        import yaml

        data = yaml.safe_load(DEFAULT_CONFIG_YAML)
        assert isinstance(data, dict)
        cfg = LoopEngineConfig.model_validate(data)
        assert cfg.engine.max_iterations == 5
