from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.schemas.tool_io import ToolLog


@dataclass
class AgentLogger:
    verbose: bool = False
    progress_enabled: bool = False
    reporter: Callable[[str], None] | None = None
    tool_logs: list[ToolLog] = field(default_factory=list)
    workflow_history: list[dict] = field(default_factory=list)

    def log_tool(self, tool_name: str, args: dict) -> None:
        self.tool_logs.append(ToolLog(tool_name=tool_name, args=args))
        self.emit(f"[tool] {tool_name} {args}")

    def log_workflow_node(self, node_id: str, node_type: str, name: str, status: str) -> None:
        self.workflow_history.append(
            {"node_id": node_id, "node_type": node_type, "name": name, "status": status}
        )
        self.emit(f"[workflow] node={node_id} type={node_type} name={name} status={status}")

    def emit(self, message: str) -> None:
        if self.reporter and (self.verbose or self.progress_enabled):
            self.reporter(message)
