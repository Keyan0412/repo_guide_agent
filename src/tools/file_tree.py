from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.tools.repo_walk import iter_repo_entries


@dataclass
class FileTreeResult:
    tree_text: str
    file_count: int
    top_level_entries: list[str]


def get_file_tree(root_path: str, max_depth: int = 3) -> FileTreeResult:
    root = Path(root_path).resolve()
    lines = [root.name + "/"]
    file_count = 0
    top_level: list[str] = []

    for child in iter_repo_entries(root, max_depth=max_depth, files_only=False):
        rel = child.relative_to(root)
        depth = len(rel.parts)
        indent = "  " * depth
        suffix = "/" if child.is_dir() else ""
        lines.append(f"{indent}{rel.name}{suffix}")
        if depth == 1:
            top_level.append(child.name + suffix)
        if child.is_file():
            file_count += 1

    return FileTreeResult(
        tree_text="\n".join(lines),
        file_count=file_count,
        top_level_entries=top_level,
    )
