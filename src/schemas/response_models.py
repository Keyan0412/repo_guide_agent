from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WorkflowNode(BaseModel):
    node_id: str
    node_type: Literal["skill", "checkpoint"] = "skill"
    name: str
    args: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: str = "always"


class ExecutionPlan(BaseModel):
    intent: str
    entry_node_id: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @property
    def selected_skills(self) -> list[WorkflowNode]:
        return [node for node in self.nodes if node.node_type == "skill"]

    def get_node(self, node_id: str) -> WorkflowNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(f"Unknown workflow node: {node_id}")


class ParsedQuery(BaseModel):
    # basic
    repo_path: str = ""
    question: str | None = None

    # question classification
    objective: str = "answer_repo_question"
    answer_mode: str = "direct_answer"

    # requirements/hints
    required_evidence: list[str] = Field(default_factory=list)
    investigation_focus: list[str] = Field(default_factory=list)
