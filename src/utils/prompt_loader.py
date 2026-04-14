from __future__ import annotations

from pathlib import Path


def load_prompt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def render_prompt(path: str, replacements: dict[str, str] | None = None) -> str:
    content = load_prompt(path)
    for key, value in (replacements or {}).items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content
