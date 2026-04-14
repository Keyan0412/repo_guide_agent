from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    repo_path: str
    question: str | None = None
    user_goal: str | None = None
    module_path: str | None = None
    symbol_name: str | None = None
    entry_type: str | None = None


class SkillOutput(BaseModel):
    skill_name: str
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
