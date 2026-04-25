from __future__ import annotations

from src.skills.base import BaseSkill


class GenerateReadingPlanSkill(BaseSkill):
    name = "generate_reading_plan"

    def output_schema_text(self) -> str:
        return """
{
  "user_goal": "string",
  "evidence": ["string"],
  "reading_steps": [
    {
      "order": 1,
      "path": "string",
      "why_read": "string",
      "focus_points": ["string"]
    }
  ],
  "suggested_stop_condition": "string",
  "uncertainties": ["string"]
}
""".strip()
