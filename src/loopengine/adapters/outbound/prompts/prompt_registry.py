"""Concrete prompt registry adapter.

Provides in-memory prompt storage with variable substitution,
versioning, caching, and validation.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from loopengine.core.domain.exceptions.prompt_exceptions import (
    PromptNotFoundError,
    PromptValidationError,
)
from loopengine.core.ports.outbound.prompt_port import (
    PromptRegistry,
    PromptTemplate,
    PromptVersion,
)

_VARIABLE_PATTERN = re.compile(r"\{(\w+)\}")


class InMemoryPromptRegistry(PromptRegistry):
    """In-memory implementation of the prompt registry.

    Stores prompt templates keyed by name with version history. Supports
    variable substitution, caching, and tag-based filtering.
    """

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, PromptTemplate]] = defaultdict(dict)
        self._cache: dict[str, str] = {}

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.name][template.version] = template
        self._invalidate(template.name)

    def get(self, name: str, version: str | None = None) -> PromptTemplate:
        versions = self._templates.get(name)
        if not versions:
            raise PromptNotFoundError(name, version or "")
        if version:
            if version not in versions:
                raise PromptNotFoundError(name, version)
            return versions[version]
        return self._latest(name)

    def list_prompts(self, *, tag: str | None = None) -> list[PromptTemplate]:
        result: list[PromptTemplate] = []
        for versions in self._templates.values():
            latest = self._latest_from_dict(versions)
            if latest is None:
                continue
            if tag and tag not in latest.tags:
                continue
            result.append(latest)
        return result

    def list_versions(self, name: str) -> list[PromptVersion]:
        versions = self._templates.get(name)
        if not versions:
            raise PromptNotFoundError(name)
        return sorted(
            [
                PromptVersion(version=v, content=t.content, changelog="")
                for v, t in versions.items()
            ],
            key=lambda pv: pv.version,
        )

    def render(self, name: str, variables: dict[str, Any] | None = None) -> str:
        template = self.get(name)
        content = template.content
        required = set(template.variables)
        provided = set(variables or {})
        missing = required - provided
        if missing:
            raise PromptValidationError(name, [f"missing variable: {v}" for v in sorted(missing)])
        cache_key = f"{name}:{hash(frozenset((variables or {}).items()))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        result = content
        for var_name, var_value in (variables or {}).items():
            result = result.replace(f"{{{var_name}}}", str(var_value))
        self._cache[cache_key] = result
        return result

    def invalidate_cache(self, name: str | None = None) -> None:
        if name is None:
            self._cache.clear()
        else:
            self._invalidate(name)

    def _latest(self, name: str) -> PromptTemplate:
        versions = self._templates.get(name)
        if not versions:
            raise PromptNotFoundError(name)
        return self._latest_from_dict(versions)  # type: ignore[return-value]

    def _latest_from_dict(self, versions: dict[str, PromptTemplate]) -> PromptTemplate | None:
        if not versions:
            return None
        latest_key = max(versions.keys())
        return versions[latest_key]

    def _invalidate(self, name: str) -> None:
        keys_to_remove = [k for k in self._cache if k.startswith(f"{name}:")]
        for k in keys_to_remove:
            del self._cache[k]
