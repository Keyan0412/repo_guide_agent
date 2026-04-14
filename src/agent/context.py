from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.schemas.skill_io import SkillOutput
from src.schemas.tool_io import ToolLog


@dataclass
class AgentContext:
    repo_path: str
    verbose: bool = False
    reporter: Callable[[str], None] | None = None
    read_files: set[str] = field(default_factory=set)
    previous_results: dict[str, SkillOutput] = field(default_factory=dict)
    uncertainties: list[str] = field(default_factory=list)
    tool_logs: list[ToolLog] = field(default_factory=list)

    def log_tool(self, tool_name: str, args: dict) -> None:
        self.tool_logs.append(ToolLog(tool_name=tool_name, args=args))
        self.emit(f"[tool] {tool_name} {args}")

    def emit(self, message: str) -> None:
        if self.verbose and self.reporter:
            self.reporter(message)
