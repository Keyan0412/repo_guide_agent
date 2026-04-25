from __future__ import annotations

from src.skills.base import BaseSkill


class SummarizeRepoSkill(BaseSkill):
    name = "summarize_repo"

    def output_schema_text(self) -> str:
        return """
{
  "repo_name": "string",
  "likely_purpose": "string",
  "evidence": ["string"],
  "primary_language": "string",
  "frameworks": ["string"],
  "project_type": "web|cli|training|library|unknown",
  "top_level_modules": [{"path": "string", "role": "string"}],
  "run_commands": ["string"],
  "key_evidence": ["string"],
  "uncertainties": ["string"]
}
""".strip()
