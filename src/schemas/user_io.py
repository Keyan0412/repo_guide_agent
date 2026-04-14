from __future__ import annotations

from pydantic import BaseModel


class UserQueryInput(BaseModel):
    repo_path: str
    question: str | None = None
