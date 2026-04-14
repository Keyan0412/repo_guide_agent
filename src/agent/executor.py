from __future__ import annotations

from typing import Callable

from src.agent.context import AgentContext
from src.agent.query_parser import QueryParser
from src.llm.client import LLMClient
from src.schemas.response_models import ParsedQuery
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.explain_module import ExplainModuleSkill
from src.skills.find_entrypoints import FindEntrypointsSkill
from src.skills.generate_reading_plan import GenerateReadingPlanSkill
from src.skills.summarize_repo import SummarizeRepoSkill
from src.skills.trace_symbol import TraceSymbolSkill


class Executor:
    def __init__(self, llm_client: LLMClient | None = None, reporter: Callable[[str], None] | None = None) -> None:
        llm_client = llm_client or LLMClient()
        self.reporter = reporter
        self.query_parser = QueryParser(llm_client=llm_client, reporter=reporter)
        self.skills = {
            "summarize_repo": SummarizeRepoSkill(llm_client=llm_client),
            "find_entrypoints": FindEntrypointsSkill(llm_client=llm_client),
            "explain_module": ExplainModuleSkill(llm_client=llm_client),
            "trace_symbol": TraceSymbolSkill(llm_client=llm_client),
            "generate_reading_plan": GenerateReadingPlanSkill(llm_client=llm_client),
        }

    def execute_plan(
        self,
        parsed_query: ParsedQuery,
        plan,
        verbose: bool = False,
    ) -> tuple[AgentContext, list[SkillOutput]]:
        context = AgentContext(repo_path=parsed_query.repo_path, verbose=verbose, reporter=self.reporter)
        context.emit(f"[executor:start] repo={parsed_query.repo_path}")
        outputs: list[SkillOutput] = []
        for call in plan.selected_skills:
            context.emit(f"[executor] running skill={call.name} args={call.args}")
            merged_input = self._build_skill_input(parsed_query, call.args)
            output = self.skills[call.name].run(merged_input, context)
            outputs.append(output)
        context.emit("[executor:done] all skills completed")
        return context, outputs

    def _build_skill_input(self, parsed_query: ParsedQuery, call_args: dict) -> SkillInput:
        base = SkillInput(
            repo_path=parsed_query.repo_path,
            question=parsed_query.question,
            user_goal=parsed_query.user_goal,
            module_path=parsed_query.module_path,
            symbol_name=parsed_query.symbol_name,
            entry_type=parsed_query.entry_type,
        )
        return base.model_copy(update=call_args)
