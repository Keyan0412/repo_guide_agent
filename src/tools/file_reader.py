from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_READ_LINES = 300


@dataclass
class ReadFileResult:
    path: str
    start_line: int
    end_line: int
    total_lines: int
    content: str


@dataclass
class ReadFilesResult:
    files: list[ReadFileResult]
    errors: list["ReadFileError"]


@dataclass
class ReadFileError:
    path: str
    error: str


def read_file(file_path: str, start_line: int = 1, end_line: int | None = None) -> ReadFileResult:
    path = Path(file_path).resolve()
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    total_lines = len(lines)
    start = max(start_line, 1)
    end = min(end_line or start + MAX_READ_LINES - 1, start + MAX_READ_LINES - 1, total_lines)
    selected = lines[start - 1 : end]
    rendered = "\n".join(f"{idx}: {line}" for idx, line in enumerate(selected, start))
    return ReadFileResult(
        path=str(path),
        start_line=start,
        end_line=end,
        total_lines=total_lines,
        content=rendered,
    )


def read_files(paths: list[str], start_line: int = 1, end_line: int | None = None) -> ReadFilesResult:
    files: list[ReadFileResult] = []
    errors: list[ReadFileError] = []
    for path in paths:
        try:
            files.append(read_file(path, start_line=start_line, end_line=end_line))
        except Exception as exc:
            errors.append(ReadFileError(path=str(Path(path).resolve()), error=f"{type(exc).__name__}: {exc}"))
    return ReadFilesResult(files=files, errors=errors)
