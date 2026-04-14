from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.tools.path_filter import should_ignore


@dataclass
class SymbolHit:
    path: str
    line: int
    kind: str
    snippet: str


DEFINITION_PATTERNS = [
    r"^\s*def\s+{symbol}\b",
    r"^\s*class\s+{symbol}\b",
    r"^\s*function\s+{symbol}\b",
    r"^\s*const\s+{symbol}\s*=",
    r"^\s*export\s+function\s+{symbol}\b",
    r"^\s*func\s+{symbol}\b",
]


def search_symbol(root_path: str, symbol_name: str, top_k: int = 20) -> dict[str, list[SymbolHit]]:
    root = Path(root_path).resolve()
    definition_regexes = [re.compile(p.format(symbol=re.escape(symbol_name))) for p in DEFINITION_PATTERNS]
    reference_regex = re.compile(rf"\b{re.escape(symbol_name)}\b")
    definitions: list[SymbolHit] = []
    references: list[SymbolHit] = []

    for path in root.rglob("*"):
        if len(definitions) + len(references) >= top_k * 2:
            break
        if not path.is_file() or should_ignore(path, root):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, 1):
            if any(regex.search(line) for regex in definition_regexes):
                definitions.append(SymbolHit(str(path.relative_to(root)), idx, "definition", line.strip()))
            elif reference_regex.search(line):
                references.append(SymbolHit(str(path.relative_to(root)), idx, "reference", line.strip()))
            if len(definitions) >= top_k and len(references) >= top_k:
                break

    return {"definitions": definitions[:top_k], "references": references[:top_k]}
