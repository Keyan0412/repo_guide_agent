from __future__ import annotations

from src.agent.context import AgentContext
from src.agent.logger import AgentLogger
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill


class VerifyAnswerSkill(BaseSkill):
    name = "verify_answer"

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext, logger: AgentLogger) -> SkillOutput | None:
        return self._run_structured_llm(
            skill_input=skill_input,
            context=context,
            logger=logger,
            system_prompt_path="prompts/system/verify_answer.md",
            max_output_tokens=900,
        )

    @staticmethod
    def build_state_updates(result: dict, skill_input: SkillInput, context: AgentContext) -> dict:
        verdict = str(result.get("verdict", "needs_more_evidence"))
        recommended_focus = result.get("recommended_focus", [])
        return {
            "answer_ready": verdict == "ready",
            "verification_result": result,
            "open_questions": recommended_focus if isinstance(recommended_focus, list) else [],
            "verifier_feedback": {
                "missing_points": result.get("missing_points", []),
                "unsupported_claims": result.get("unsupported_claims", []),
            },
        }

    @staticmethod
    def build_next_actions(result: dict, skill_input: SkillInput, context: AgentContext) -> list[str]:
        recommended_focus = result.get("recommended_focus", [])
        return [str(item) for item in recommended_focus] if isinstance(recommended_focus, list) else []

    @staticmethod
    def output_schema_text() -> str:
        return """
{
  "verdict": "ready|needs_more_evidence",
  "coverage_ok": true,
  "evidence": ["string"],
  "missing_points": ["string"],
  "unsupported_claims": ["string"],
  "recommended_focus": ["string"],
  "uncertainties": ["string"]
}
""".strip()
