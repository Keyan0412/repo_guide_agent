from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.tools.repo_walk import RepoWalkError, iter_repo_entries


@dataclass
class SearchHit:
    path: str
    line: int
    snippet: str


@dataclass
class KeywordSearchResult:
    hits: list[SearchHit]
    errors: list[RepoWalkError]


def search_keyword(root_path: str, query: str, top_k: int = 20) -> KeywordSearchResult:
    root = Path(root_path).resolve()
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    hits: list[SearchHit] = []
    errors: list[RepoWalkError] = []
    for event in iter_repo_entries(root, files_only=True):
        if len(hits) >= top_k:
            break
        if isinstance(event, RepoWalkError):
            errors.append(event)
            continue
        path = event.path
        try:
            for idx, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if pattern.search(line):
                    hits.append(SearchHit(path=str(path.relative_to(root)), line=idx, snippet=line.strip()))
                    if len(hits) >= top_k:
                        break
        except OSError as exc:
            errors.append(
                RepoWalkError(
                    path=str(path.relative_to(root)),
                    operation="read_text",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            continue
    return KeywordSearchResult(hits=hits, errors=errors)
