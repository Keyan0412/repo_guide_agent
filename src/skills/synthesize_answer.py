from __future__ import annotations

from src.agent.context import AgentContext
from src.agent.logger import AgentLogger
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill


class SynthesizeAnswerSkill(BaseSkill):
    name = "synthesize_answer"

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext, logger: AgentLogger) -> SkillOutput | None:
        return self._run_structured_llm(
            skill_input=skill_input,
            context=context,
            logger=logger,
            system_prompt_path="prompts/system/synthesize_answer.md",
            max_output_tokens=1400,
        )

    @staticmethod
    def build_state_updates(result: dict, skill_input: SkillInput, context: AgentContext) -> dict:
        return {
            "draft_answer": result.get("answer_markdown"),
            "coverage_points": result.get("coverage_points", []),
            "open_questions": result.get("remaining_gaps", []),
            "latest_synthesized_answer": result,
        }

    @staticmethod
    def output_schema_text() -> str:
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
