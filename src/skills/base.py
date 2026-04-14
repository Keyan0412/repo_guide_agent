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
        context.emit(f"[skill] {self.name} using llm agent")
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
        )
        if result is None:
            return None
        evidence = _collect_evidence(result)
        uncertainties = result.get("uncertainties", []) if isinstance(result.get("uncertainties"), list) else []
        return SkillOutput(skill_name=self.name, data=result, evidence=evidence, uncertainties=uncertainties)

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
                "user_goal": skill_input.user_goal,
                "module_path": skill_input.module_path,
                "symbol_name": skill_input.symbol_name,
                "entry_type": skill_input.entry_type,
                "previous_results": previous,
            },
            ensure_ascii=False,
            indent=2,
        )

    @abstractmethod
    def output_schema_text(self) -> str:
        raise NotImplementedError


def _collect_evidence(result: dict[str, Any]) -> list[str]:
    if isinstance(result.get("key_evidence"), list):
        return [str(item) for item in result["key_evidence"][:8]]
    if isinstance(result.get("supporting_evidence"), list):
        return [str(item) for item in result["supporting_evidence"][:8]]
    if isinstance(result.get("entry_candidates"), list):
        evidence: list[str] = []
        for item in result["entry_candidates"][:3]:
            for value in item.get("supporting_evidence", [])[:2]:
                evidence.append(str(value))
        return evidence
    return []
