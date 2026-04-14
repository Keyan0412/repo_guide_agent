from __future__ import annotations

from pydantic import BaseModel, Field


class SkillCall(BaseModel):
    name: str
    args: dict = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    intent: str
    selected_skills: list[SkillCall]
    notes: list[str] = Field(default_factory=list)


class ParsedQuery(BaseModel):
    repo_path: str = ""
    question: str | None = None
    intent: str = "summarize_repo"
    module_path: str | None = None
    symbol_name: str | None = None
    user_goal: str | None = None
    entry_type: str | None = None
    confidence: float = 0.0
    notes: list[str] = Field(default_factory=list)
