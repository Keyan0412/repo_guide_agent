from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.tools.path_filter import DEFAULT_IGNORE_DIRS, should_ignore


@dataclass
class FileTreeResult:
    tree_text: str
    file_count: int
    top_level_entries: list[str]


def _walk(path: Path, root: Path, depth: int, max_depth: int, lines: list[str], stats: dict[str, int]) -> None:
    if depth > max_depth:
        return
    children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for child in children:
        if should_ignore(child, root, DEFAULT_IGNORE_DIRS):
            continue
        rel = child.relative_to(root)
        indent = "  " * depth
        suffix = "/" if child.is_dir() else ""
        lines.append(f"{indent}{rel.name}{suffix}")
        if child.is_file():
            stats["file_count"] += 1
        elif depth < max_depth:
            _walk(child, root, depth + 1, max_depth, lines, stats)


def get_file_tree(root_path: str, max_depth: int = 3) -> FileTreeResult:
    root = Path(root_path).resolve()
    lines = [root.name + "/"]
    stats = {"file_count": 0}
    _walk(root, root, 1, max_depth, lines, stats)
    top_level = []
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if should_ignore(child, root, DEFAULT_IGNORE_DIRS):
            continue
        top_level.append(child.name + ("/" if child.is_dir() else ""))
    return FileTreeResult(
        tree_text="\n".join(lines),
        file_count=stats["file_count"],
        top_level_entries=top_level,
    )
