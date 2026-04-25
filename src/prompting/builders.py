from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.agent.context import AgentContext
from src.schemas.response_models import ParsedQuery
from src.schemas.skill_io import SkillInput, SkillOutput
from src.schemas.user_io import UserQueryInput
from src.utils.prompt_loader import render_prompt


@dataclass(frozen=True)
class PromptSpec:
    system_prompt: str
    user_prompt: str


def build_query_parser_prompt(user_input: UserQueryInput) -> PromptSpec:
    return PromptSpec(
        system_prompt=render_prompt(
            "prompts/system/query_parser.md",
            {
                "OUTPUT_SCHEMA": json.dumps(ParsedQuery.model_json_schema(), ensure_ascii=False, indent=2),
            },
        ),
        user_prompt=_dump_payload({"question": user_input.question}),
    )


def build_skill_agent_prompt(
    *,
    skill_name: str,
    output_schema: str,
    skill_input: SkillInput,
    context: AgentContext,
) -> PromptSpec:
    prompt_path = Path("prompts/skills") / f"{skill_name}.md"
    skill_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    return PromptSpec(
        system_prompt=render_prompt(
            "prompts/system/skill_agent.md",
            {
                "SKILL_NAME": skill_name,
                "SKILL_PROMPT": skill_prompt,
                "OUTPUT_SCHEMA": output_schema,
            },
        ),
        user_prompt=_build_skill_user_prompt(skill_input, context),
    )


def build_structured_skill_prompt(
    *,
    system_prompt_path: str,
    output_schema: str,
    skill_input: SkillInput,
    context: AgentContext,
) -> PromptSpec:
    return PromptSpec(
        system_prompt=render_prompt(system_prompt_path, {"OUTPUT_SCHEMA": output_schema}),
        user_prompt=_build_skill_user_prompt(skill_input, context),
    )


def build_response_formatter_prompt(
    outputs: list[SkillOutput],
    context: AgentContext,
    question: str | None = None,
) -> PromptSpec:
    return PromptSpec(
        system_prompt=render_prompt("prompts/system/response_formatter.md"),
        user_prompt=_dump_payload(
            {
                "question": question,
                "repo_path": context.repo_path,
                "skill_outputs": [output.model_dump() for output in outputs],
                "tool_log_count": len(context.tool_logs),
                "uncertainties": context.uncertainties,
                "workflow_state": context.workflow_state,
                "workflow_history": context.workflow_history,
            }
        ),
    )


def _build_skill_user_prompt(skill_input: SkillInput, context: AgentContext) -> str:
    previous = {name: output.data for name, output in context.previous_results.items()}
    return _dump_payload(
        {
            "repo_path": skill_input.repo_path,
            "question": skill_input.question,
            "objective": skill_input.objective,
            "answer_mode": skill_input.answer_mode,
            "required_evidence": skill_input.required_evidence,
            "investigation_focus": skill_input.investigation_focus,
            "workflow_state": skill_input.workflow_state,
            "previous_results": previous,
        }
    )


def _dump_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
