from __future__ import annotations

from pathlib import Path


def shorten(text: str, limit: int = 240) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def repo_name(path: Path) -> str:
    return path.resolve().name
