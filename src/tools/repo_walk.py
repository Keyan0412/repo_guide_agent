from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterator
from pathlib import Path


@dataclass
class RepoWalkEntry:
    path: Path


@dataclass
class RepoWalkError:
    path: str
    operation: str
    error_type: str
    message: str


RepoWalkEvent = RepoWalkEntry | RepoWalkError


def iter_repo_entries(
    start: Path,
    *,
    max_depth: int | None = None,
    files_only: bool = False,
) -> Iterator[RepoWalkEvent]:
    start = start.resolve()

    if start.is_file():
        yield RepoWalkEntry(path=start)
        return

    yield from _iter_dir_entries(start, max_depth=max_depth, files_only=files_only, depth=1)


def _iter_dir_entries(
    current: Path,
    *,
    max_depth: int | None,
    files_only: bool,
    depth: int,
) -> Iterator[RepoWalkEvent]:
    try:
        children = sorted(current.iterdir(), key=lambda path: (path.is_file(), path.name.lower()))
    except OSError as exc:
        yield RepoWalkError(
            path=str(current),
            operation="iterdir",
            error_type=type(exc).__name__,
            message=str(exc),
        )
        return

    for child in children:
        if not files_only or child.is_file():
            yield RepoWalkEntry(path=child)
        if child.is_dir() and (max_depth is None or depth < max_depth):
            yield from _iter_dir_entries(child, max_depth=max_depth, files_only=files_only, depth=depth + 1)
