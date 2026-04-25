from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.utils.prompt_loader import render_prompt


class SynthesizeAnswerSkill(BaseSkill):
    name = "synthesize_answer"

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput | None:
        system_prompt = render_prompt(
            "prompts/system/synthesize_answer.md",
            {"OUTPUT_SCHEMA": self.output_schema_text()},
        )
        result = self.llm_client.generate_json(
            system_prompt=system_prompt,
            user_prompt=self.build_user_prompt(skill_input, context),
            max_output_tokens=1400,
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
        )

    def build_state_updates(self, result: dict, skill_input: SkillInput, context: AgentContext) -> dict:
        return {
            "draft_answer": result.get("answer_markdown"),
            "coverage_points": result.get("coverage_points", []),
            "open_questions": result.get("remaining_gaps", []),
            "latest_synthesized_answer": result,
        }

    def output_schema_text(self) -> str:
        return """
{
  "answer_title": "string|null",
  "answer_markdown": "string",
  "evidence": ["string"],
  "coverage_points": ["string"],
  "remaining_gaps": ["string"],
  "uncertainties": ["string"]
}
""".strip()
