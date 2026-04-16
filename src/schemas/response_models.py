from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillCall(BaseModel):
    name: str
    args: dict = Field(default_factory=dict)


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
    def selected_skills(self) -> list[SkillCall]:
        return [SkillCall(name=node.name, args=node.args) for node in self.nodes if node.node_type == "skill"]

    def get_node(self, node_id: str) -> WorkflowNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(f"Unknown workflow node: {node_id}")


class ParsedQuery(BaseModel):
    repo_path: str = ""
    question: str | None = None
    intent: str = "answer_repo_question"
    objective: str = "answer_repo_question"
    answer_mode: str = "direct_answer"
    module_path: str | None = None
    symbol_name: str | None = None
    user_goal: str | None = None
    entry_type: str | None = None
    key_entities: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    investigation_focus: list[str] = Field(default_factory=list)
    expected_sections: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: list[str] = Field(default_factory=list)
