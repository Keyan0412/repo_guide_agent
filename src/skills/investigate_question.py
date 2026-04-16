from __future__ import annotations

from typing import Any

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput
from src.skills.base import BaseSkill


class InvestigateQuestionSkill(BaseSkill):
    name = "investigate_question"

    def build_state_updates(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> dict[str, Any]:
        findings = result.get("findings", [])
        evidence_gaps = result.get("evidence_gaps", [])
        return {
            "latest_investigation": result,
            "findings": findings if isinstance(findings, list) else [],
            "open_questions": evidence_gaps if isinstance(evidence_gaps, list) else [],
            "investigation_summary": result.get("investigation_summary"),
        }

    def build_next_actions(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> list[str]:
        evidence_gaps = result.get("evidence_gaps", [])
        return [str(item) for item in evidence_gaps] if isinstance(evidence_gaps, list) else []

    def build_fallback_result(
        self,
        skill_input: SkillInput,
        context: AgentContext,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        open_questions = skill_input.workflow_state.get("open_questions", [])
        findings = skill_input.workflow_state.get("findings", [])
        fallback_claim = f"Collected evidence for objective `{skill_input.objective or 'general_repository_question'}`."
        if skill_input.question:
            fallback_claim = f"Collected repository evidence to answer: {skill_input.question}"
        return {
            "investigation_summary": "The model completed tool-based evidence collection but failed to emit fully valid JSON; using a minimal recovered investigation result.",
            "findings": findings[:6] if isinstance(findings, list) else [
                {
                    "claim": fallback_claim,
                    "importance": "medium",
                    "evidence": sorted(context.read_files)[:4],
                    "related_files": sorted(context.read_files)[:4],
                }
            ],
            "evidence_gaps": [str(item) for item in open_questions[:6]] if isinstance(open_questions, list) else [],
            "uncertainties": ["LLM output formatting was unstable; investigation result was minimally recovered."],
        }

    def output_schema_text(self) -> str:
        return """
{
  "investigation_summary": "string",
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
