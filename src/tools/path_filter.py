from __future__ import annotations

from pathlib import Path


DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "coverage",
}

DEFAULT_IGNORE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
}

DEFAULT_BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".gz",
    ".tar",
    ".so",
    ".dll",
    ".dylib",
}


def should_ignore(path: Path, root: Path, ignore_patterns: set[str] | None = None) -> bool:
    ignore_patterns = ignore_patterns or DEFAULT_IGNORE_DIRS
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    if relative.name in DEFAULT_IGNORE_FILES or relative.name.startswith(".env."):
        return True
    parts = set(relative.parts)
    if parts & ignore_patterns:
        return True
    if any(part.endswith(".egg-info") for part in relative.parts):
        return True
    return path.suffix.lower() in DEFAULT_BINARY_EXTENSIONS
