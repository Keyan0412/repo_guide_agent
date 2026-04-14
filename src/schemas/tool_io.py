from __future__ import annotations

from pydantic import BaseModel


class ToolLog(BaseModel):
    tool_name: str
    args: dict
