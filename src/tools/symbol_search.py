from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from src.tools.repo_walk import RepoWalkError, iter_repo_entries


@dataclass
class SymbolHit:
    path: str
    line: int
    kind: str
    match_type: str
    snippet: str


@dataclass
class SymbolSearchResult:
    language: str
    supported: bool
    message: str | None
    definitions: list[SymbolHit]
    references: list[SymbolHit]
    errors: list[RepoWalkError]


def search_symbol(root_path: str, symbol_name: str, language: str, top_k: int = 20) -> SymbolSearchResult:
    normalized_language = language.strip().lower()
    if normalized_language == "python":
        return search_symbol_python(root_path, symbol_name, top_k=top_k)

    return SymbolSearchResult(
        language=normalized_language,
        supported=False,
        message=f"Unsupported language: {language}",
        definitions=[],
        references=[],
        errors=[],
    )


def search_symbol_python(root_path: str, symbol_name: str, top_k: int = 20) -> SymbolSearchResult:
    root = Path(root_path).resolve()
    reference_regex = re.compile(rf"\b{re.escape(symbol_name)}\b")
    definitions: list[SymbolHit] = []
    references: list[SymbolHit] = []
    errors: list[RepoWalkError] = []

    for event in iter_repo_entries(root, files_only=True):
        if len(definitions) + len(references) >= top_k * 2:
            break
        if isinstance(event, RepoWalkError):
            errors.append(event)
            continue
        path = event.path
        if path.suffix != ".py":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
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
        lines = text.splitlines()
        file_definitions = _find_python_definitions(path, root, symbol_name, lines, text)
        definitions.extend(file_definitions)
        definition_lines = {hit.line for hit in file_definitions}
        reference_match_types = _find_python_reference_match_types(symbol_name, text)

        for idx, line in enumerate(lines, 1):
            if idx in definition_lines:
                continue
            if reference_regex.search(line):
                references.append(
                    SymbolHit(
                        str(path.relative_to(root)),
                        idx,
                        "reference",
                        reference_match_types.get(idx, "path_or_text_mention"),
                        line.strip(),
                    )
                )
            if len(definitions) >= top_k and len(references) >= top_k:
                break

    return SymbolSearchResult(
        language="python",
        supported=True,
        message=None,
        definitions=definitions[:top_k],
        references=references[:top_k],
        errors=errors,
    )


def _find_python_definitions(
    path: Path,
    root: Path,
    symbol_name: str,
    lines: list[str],
    text: str,
) -> list[SymbolHit]:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []

    definitions: list[SymbolHit] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol_name:
            lineno = getattr(node, "lineno", 1)
            snippet = lines[lineno - 1].strip() if 0 < lineno <= len(lines) else ""
            definitions.append(
                SymbolHit(str(path.relative_to(root)), lineno, "definition", "python_ast_definition", snippet)
            )
    return definitions


def _find_python_reference_match_types(symbol_name: str, text: str) -> dict[int, str]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {}

    priorities = {
        "path_or_text_mention": 0,
        "module_or_alias": 1,
        "direct_identifier": 2,
    }
    matches: dict[int, str] = {}

    def record(lineno: int | None, match_type: str) -> None:
        if lineno is None:
            return
        current = matches.get(lineno)
        if current is None or priorities[match_type] > priorities[current]:
            matches[lineno] = match_type

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == symbol_name:
            record(getattr(node, "lineno", None), "direct_identifier")
        elif isinstance(node, ast.Attribute) and node.attr == symbol_name:
            record(getattr(node, "lineno", None), "module_or_alias")
        elif isinstance(node, ast.alias):
            alias_parts = node.name.split(".")
            if symbol_name in alias_parts or node.asname == symbol_name:
                record(getattr(node, "lineno", None), "module_or_alias")

    return matches
