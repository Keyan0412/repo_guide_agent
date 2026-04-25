from __future__ import annotations

from src.skills.base import BaseSkill


class FindEntrypointsSkill(BaseSkill):
    name = "find_entrypoints"

    def output_schema_text(self) -> str:
        return """
{
  "evidence": ["string"],
  "entry_candidates": [
    {
      "path": "string",
      "entry_type": "web|cli|training|service|unknown",
      "confidence": 0.0,
      "reason": "string",
      "supporting_evidence": ["string"]
    }
  ],
  "recommended_first_read": ["string"],
  "uncertainties": ["string"]
}
""".strip()
