from __future__ import annotations

from pathlib import Path


LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cpp": "C++",
    ".c": "C",
}


def detect_primary_language(extension_stats: dict[str, int], root: Path) -> str:
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        return "Python"
    if (root / "package.json").exists():
        return "TypeScript" if extension_stats.get(".ts", 0) >= extension_stats.get(".js", 0) else "JavaScript"
    best = "Unknown"
    best_count = -1
    for suffix, count in extension_stats.items():
        language = LANGUAGE_BY_SUFFIX.get(suffix)
        if language and count > best_count:
            best = language
            best_count = count
    return best
