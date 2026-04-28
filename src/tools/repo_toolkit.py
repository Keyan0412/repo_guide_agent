from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from openai.types.chat import ChatCompletionToolParam

from src.agent.logger import AgentLogger
from src.tools.file_reader import read_files
from src.tools.file_tree import get_file_tree
from src.tools.keyword_search import search_keyword
from src.tools.symbol_search import search_symbol


def build_tool_schemas() -> list[ChatCompletionToolParam]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_file_tree",
                "description": "Get a repo file tree under a given path with limited depth.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "max_depth": {"type": "integer", "minimum": 1, "maximum": 5},
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_files",
                "description": "Read multiple files in one tool call.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                        "start_line": {"type": "integer", "minimum": 1},
                        "end_line": {"type": "integer", "minimum": 1},
                    },
                    "required": ["paths"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_keyword",
                "description": "Search keyword occurrences in the repo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_symbol",
                "description": "Search possible definitions and references for a symbol in a specific language.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol_name": {"type": "string"},
                        "language": {"type": "string"},
                        "top_k": {"type": "integer", "minimum": 1, "maximum": 50},
                    },
                    "required": ["symbol_name", "language"],
                },
            },
        },
    ]


class RepoToolkit:
    def __init__(self, repo_path: str, logger: AgentLogger, read_files_registry: set[str]) -> None:
        self.repo_root = Path(repo_path).resolve()
        self.logger = logger
        self.read_files_registry = read_files_registry

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if tool_name == "get_file_tree":
                target = self._resolve(arguments.get("path", "."))
                max_depth = int(arguments.get("max_depth", 3))
                self.logger.log_tool(tool_name, {"path": str(target), "max_depth": max_depth})
                result = get_file_tree(str(target), max_depth=max_depth)
                return _serialize(result)
            if tool_name == "read_files":
                raw_paths = arguments.get("paths") or []
                if not isinstance(raw_paths, list) or not raw_paths:
                    raise ValueError("read_files requires a non-empty paths array")
                targets = [self._resolve(path) for path in raw_paths]
                start_line = int(arguments.get("start_line", 1))
                end_line = arguments.get("end_line")
                end_line = int(end_line) if end_line else None
                self.logger.log_tool(
                    tool_name,
                    {
                        "paths": [str(target) for target in targets],
                        "start_line": start_line,
                        "end_line": end_line,
                    },
                )
                for target in targets:
                    self.read_files_registry.add(str(target))
                result = read_files([str(target) for target in targets], start_line=start_line, end_line=end_line)
                return _serialize(result)
            if tool_name == "search_keyword":
                query = str(arguments.get("query", ""))
                top_k = int(arguments.get("top_k", 10))
                self.logger.log_tool(tool_name, {"query": query, "top_k": top_k})
                return _serialize(search_keyword(str(self.repo_root), query, top_k=top_k))
            if tool_name == "search_symbol":
                symbol_name = str(arguments.get("symbol_name", ""))
                language = str(arguments.get("language", ""))
                top_k = int(arguments.get("top_k", 10))
                self.logger.log_tool(tool_name, {"symbol_name": symbol_name, "language": language, "top_k": top_k})
                return _serialize(search_symbol(str(self.repo_root), symbol_name, language, top_k=top_k))
            return {"error": f"Unknown tool: {tool_name}"}
        except Exception as exc:
            self.logger.emit(f"[tool:error] {tool_name} {exc}")
            return {"error": f"{type(exc).__name__}: {exc}"}

    def _resolve(self, path: str | None) -> Path:
        if not path:
            return self.repo_root
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = (self.repo_root / candidate).resolve()
        if self.repo_root not in candidate.parents and candidate != self.repo_root:
            raise ValueError(f"Path escapes repo root: {path}")
        return candidate


def _serialize(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    return value
