from __future__ import annotations

from pathlib import Path


def render_prompt(
    path: str,
    replacements: dict[str, str] | None = None,
    *,
    missing_ok: bool = False,
) -> str:
    prompt_path = Path(path)
    if missing_ok and not prompt_path.exists():
        return ""
    content = prompt_path.read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content
