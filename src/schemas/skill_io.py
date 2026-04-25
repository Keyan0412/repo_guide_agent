from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    repo_path: str
    question: str | None = None
    objective: str | None = None
    answer_mode: str | None = None
    required_evidence: list[str] = Field(default_factory=list)
    investigation_focus: list[str] = Field(default_factory=list)
    workflow_state: dict[str, Any] = Field(default_factory=dict)


class SkillOutput(BaseModel):
    skill_name: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    state_updates: dict[str, Any] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)
