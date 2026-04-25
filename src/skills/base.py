from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.agent.context import AgentContext
from src.errors import AgentError
from src.llm.client import LLMClient
from src.prompting import build_skill_agent_prompt, build_structured_skill_prompt
from src.schemas.skill_io import SkillInput, SkillOutput
from src.tools.repo_toolkit import RepoToolkit, build_tool_schemas


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
        prompt = build_skill_agent_prompt(
            skill_name=self.name,
            output_schema=self.output_schema_text(),
            skill_input=skill_input,
            context=context,
        )
        result = self.llm_client.run_tool_agent(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            tools=build_tool_schemas(),
            tool_executor=toolkit.execute,
            progress_callback=context.emit,
        )
        return self._build_skill_output(result, skill_input, context)

    def _run_structured_llm(
        self,
        skill_input: SkillInput, context: AgentContext,
        *,
        system_prompt_path: str, max_output_tokens: int,
    ) -> SkillOutput | None:
        prompt = build_structured_skill_prompt(
            system_prompt_path=system_prompt_path,
            output_schema=self.output_schema_text(),
            skill_input=skill_input,
            context=context,
        )
        result = self.llm_client.generate_json(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            max_output_tokens=max_output_tokens,
        )
        return self._build_skill_output(result, skill_input, context)

    def _build_skill_output(
        self,
        result: dict[str, Any] | None,
        skill_input: SkillInput,
        context: AgentContext,
    ) -> SkillOutput | None:
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

    @staticmethod
    def build_state_updates(result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> dict[str, Any]:
        return {}

    @staticmethod
    def build_next_actions(result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> list[str]:
        return []

    @staticmethod
    @abstractmethod
    def output_schema_text() -> str:
        raise NotImplementedError
