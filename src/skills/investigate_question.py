from __future__ import annotations

from typing import Any

from src.agent.context import AgentContext
from src.agent.logger import AgentLogger
from src.schemas.skill_io import SkillInput
from src.skills.base import BaseSkill
from src.tools.repo_toolkit import RepoToolkit


class InvestigateQuestionSkill(BaseSkill):
    name = "investigate_question"

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext, logger: AgentLogger):
        self._bootstrap_repo_evidence(skill_input, context, logger)
        return super()._run_with_llm(skill_input, context, logger)

    @staticmethod
    def build_state_updates(result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> dict[str, Any]:
        findings = result.get("findings", [])
        evidence_gaps = result.get("evidence_gaps", [])
        return {
            "latest_investigation": result,
            "findings": findings if isinstance(findings, list) else [],
            "open_questions": evidence_gaps if isinstance(evidence_gaps, list) else [],
            "investigation_summary": result.get("investigation_summary"),
        }

    @staticmethod
    def build_next_actions(result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> list[str]:
        evidence_gaps = result.get("evidence_gaps", [])
        return [str(item) for item in evidence_gaps] if isinstance(evidence_gaps, list) else []

    @staticmethod
    def output_schema_text() -> str:
        return """
{
  "investigation_summary": "string",
  "evidence": ["string"],
  "findings": [
    {
      "claim": "string",
      "importance": "high|medium|low",
      "evidence": ["string"],
      "related_files": ["string"]
    }
  ],
  "evidence_gaps": ["string"],
  "uncertainties": ["string"]
}
""".strip()

    @staticmethod
    def _bootstrap_repo_evidence(skill_input: SkillInput, context: AgentContext, logger: AgentLogger) -> None:
        toolkit = RepoToolkit(skill_input.repo_path, logger, context.read_files)

        if not any(log.tool_name == "get_file_tree" for log in logger.tool_logs):
            toolkit.execute("get_file_tree", {"path": ".", "max_depth": 3})
