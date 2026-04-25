from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.utils.prompt_loader import render_prompt


class VerifyAnswerSkill(BaseSkill):
    name = "verify_answer"

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput | None:
        system_prompt = render_prompt(
            "prompts/system/verify_answer.md",
            {"OUTPUT_SCHEMA": self.output_schema_text()},
        )
        result = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=self.build_user_prompt(skill_input, context),
            max_output_tokens=900,
        )
        if result is None:
            return None
        evidence = result.get("evidence")
        if not isinstance(evidence, list):
            return None
        uncertainties = result.get("uncertainties", []) if isinstance(result.get("uncertainties"), list) else []
        return SkillOutput(
            skill_name=self.name,
            data=result,
            evidence=[str(item) for item in evidence],
            uncertainties=uncertainties,
            state_updates=self.build_state_updates(result, skill_input, context),
            next_actions=self.build_next_actions(result, skill_input, context),
        )

    def build_state_updates(self, result: dict, skill_input: SkillInput, context: AgentContext) -> dict:
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

    def build_next_actions(self, result: dict, skill_input: SkillInput, context: AgentContext) -> list[str]:
        recommended_focus = result.get("recommended_focus", [])
        return [str(item) for item in recommended_focus] if isinstance(recommended_focus, list) else []

    def output_schema_text(self) -> str:
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
