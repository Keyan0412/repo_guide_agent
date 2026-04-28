from __future__ import annotations

from dataclasses import dataclass, field

from src.agent.workflow_state import WorkflowState
from src.schemas.tool_io import ToolLog


@dataclass
class AgentContext:
    repo_path: str
    read_files: set[str] = field(default_factory=set)
    tool_logs: list[ToolLog] = field(default_factory=list)
    workflow_history: list[dict] = field(default_factory=list)
    workflow_state: WorkflowState = field(default_factory=WorkflowState)

    def update_workflow_state(self, updates: dict) -> None:
        if not updates:
            return
        self.workflow_state.update(updates)
