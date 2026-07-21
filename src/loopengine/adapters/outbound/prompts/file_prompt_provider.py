"""File-based prompt provider adapter.

Loads prompt templates from the filesystem. Supports markdown files
with YAML front matter for metadata and plain markdown for content.
"""

from __future__ import annotations

import re
from pathlib import Path

from loopengine.core.domain.exceptions.prompt_exceptions import PromptLoadError
from loopengine.core.ports.outbound.prompt_port import PromptProvider, PromptTemplate

_FRONT_MATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class FilePromptProvider(PromptProvider):
    """Loads prompts from a directory of markdown files.

    Each file can optionally have YAML front matter for metadata:
    ````---
    version: "1.0.0"
    variables: [goal, context]
    tags: [planning, workflow]
    description: A prompt for planning
    ---
    # Your prompt content here
    ````
    """

    def __init__(self, directory: str | Path) -> None:
        self._directory = Path(directory)

    @property
    def name(self) -> str:
        return "filesystem"

    def load_all(self) -> list[PromptTemplate]:
        if not self._directory.is_dir():
            return []
        templates: list[PromptTemplate] = []
        for md_file in sorted(self._directory.glob("*.md")):
            try:
                template = self._load_file(md_file)
                if template:
                    templates.append(template)
            except Exception as exc:
                raise PromptLoadError(md_file.stem, str(exc)) from exc
        return templates

    def load(self, name: str) -> PromptTemplate | None:
        file_path = self._directory / f"{name}.md"
        if not file_path.exists():
            return None
        try:
            return self._load_file(file_path)
        except Exception as exc:
            raise PromptLoadError(name, str(exc)) from exc

    def _load_file(self, file_path: Path) -> PromptTemplate | None:
        content = file_path.read_text(encoding="utf-8")
        name = file_path.stem
        version = "1.0.0"
        variables: list[str] = []
        tags: list[str] = []
        description = ""
        body = content

        match = _FRONT_MATTER_PATTERN.match(content)
        if match:
            front_matter = match.group(1)
            body = content[match.end() :]
            meta = self._parse_front_matter(front_matter)
            version = str(meta.get("version", "1.0.0"))
            raw_vars = meta.get("variables", [])
            variables = list(raw_vars) if isinstance(raw_vars, list) else []
            raw_tags = meta.get("tags", [])
            tags = list(raw_tags) if isinstance(raw_tags, list) else []
            description = str(meta.get("description", ""))

        if not body.strip():
            return None

        # Auto-detect variables from {var} patterns if not specified
        if not variables:
            variables = list(dict.fromkeys(re.findall(r"\{(\w+)\}", body)))

        return PromptTemplate(
            name=name,
            content=body.strip(),
            version=str(version),
            provider="filesystem",
            variables=variables,
            tags=tags,
            description=description,
        )

    @staticmethod
    def _parse_front_matter(text: str) -> dict[str, object]:
        """Minimal YAML-like parser for front matter (no PyYAML dependency)."""
        result: dict[str, object] = {}
        current_key: str | None = None
        current_list: list[str] | None = None

        for raw_line in text.split("\n"):
            stripped = raw_line.strip()
            if not stripped:
                continue

            # List continuation
            if stripped.startswith("- ") and current_key and current_list is not None:
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
                continue

            if ":" in stripped:
                # Save previous list
                if current_key and current_list is not None:
                    result[current_key] = current_list
                    current_list = None

                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()

                if not value:
                    current_key = key
                    current_list = []
                    continue

                # Parse value
                if value.startswith("[") and value.endswith("]"):
                    # Inline list: [a, b, c]
                    items = value[1:-1].split(",")
                    result[key] = [i.strip().strip('"').strip("'") for i in items if i.strip()]
                elif (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    result[key] = value[1:-1]
                elif value.isdigit():
                    result[key] = int(value)
                elif value in ("true", "false"):
                    result[key] = value == "true"
                else:
                    result[key] = value

                current_key = key

        # Save last list
        if current_key and current_list is not None:
            result[current_key] = current_list

        return result
