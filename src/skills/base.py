from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.agent.context import AgentContext
from src.errors import AgentError
from src.llm.client import LLMClient
from src.schemas.skill_io import SkillInput, SkillOutput
from src.tools.repo_toolkit import RepoToolkit, build_tool_schemas
from src.utils.prompt_loader import render_prompt


class BaseSkill(ABC):
    name: str

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        context.emit(f"[skill:start] {self.name}")
        if not self.llm_client.enabled:
            raise AgentError(f"skill:{self.name}", "LLM client is unavailable. Check OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL.")
        llm_output = self._run_with_llm(skill_input, context)
        if llm_output is None:
            raise AgentError(f"skill:{self.name}", "LLM tool-agent failed to return valid structured output.")
        context.previous_results[self.name] = llm_output
        context.emit(f"[skill:done] {self.name} via llm")
        return llm_output

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput | None:
        toolkit = RepoToolkit(skill_input.repo_path, context)
        result = self.llm_client.run_tool_agent(
            system_prompt=self.build_system_prompt(),
            user_prompt=self.build_user_prompt(skill_input, context),
            tools=build_tool_schemas(),
            tool_executor=toolkit.execute,
            progress_callback=context.emit,
            fallback_builder=lambda messages: self.build_fallback_result(skill_input, context, messages),
        )
        if result is None:
            return None
        evidence = result.get("evidence")
        if not isinstance(evidence, list):
            raise AgentError(f"skill:{self.name}", "LLM output must include an `evidence` array.")
        uncertainties = result.get("uncertainties", []) if isinstance(result.get("uncertainties"), list) else []
        return SkillOutput(
            skill_name=self.name,
            data=result,
            evidence=[str(item) for item in evidence],
            uncertainties=uncertainties,
            state_updates=self.build_state_updates(result, skill_input, context),
            next_actions=self.build_next_actions(result, skill_input, context),
        )

    def build_system_prompt(self) -> str:
        prompt_path = Path("prompts/skills") / f"{self.name}.md"
        if prompt_path.exists():
            return render_prompt(
                "prompts/system/skill_agent.md",
                {
                    "SKILL_NAME": self.name,
                    "SKILL_PROMPT": prompt_path.read_text(encoding="utf-8"),
                    "OUTPUT_SCHEMA": self.output_schema_text(),
                },
            )
        return render_prompt(
            "prompts/system/skill_agent.md",
            {
                "SKILL_NAME": self.name,
                "SKILL_PROMPT": "",
                "OUTPUT_SCHEMA": self.output_schema_text(),
            },
        )

    def build_user_prompt(self, skill_input: SkillInput, context: AgentContext) -> str:
        previous = {name: output.data for name, output in context.previous_results.items()}
        return json.dumps(
            {
                "repo_path": skill_input.repo_path,
                "question": skill_input.question,
                "objective": skill_input.objective,
                "answer_mode": skill_input.answer_mode,
                "required_evidence": skill_input.required_evidence,
                "investigation_focus": skill_input.investigation_focus,
                "workflow_state": skill_input.workflow_state,
                "previous_results": previous,
            },
            ensure_ascii=False,
            indent=2,
        )

    def build_state_updates(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> dict[str, Any]:
        return {}

    def build_next_actions(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> list[str]:
        return []

    def build_fallback_result(self, skill_input: SkillInput, context: AgentContext, messages: list[dict[str, Any]]) -> dict[str, Any] | None:
        return None

    @abstractmethod
    def output_schema_text(self) -> str:
        raise NotImplementedError
