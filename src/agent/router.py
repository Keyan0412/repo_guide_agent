from __future__ import annotations

from typing import Callable

from src.agent.query_parser import QueryParser
from src.llm.client import LLMClient
from src.schemas.response_models import ExecutionPlan, ParsedQuery, SkillCall
from src.schemas.user_io import UserQueryInput


class Router:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        reporter: Callable[[str], None] | None = None,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.reporter = reporter
        self.query_parser = QueryParser(llm_client=self.llm_client, reporter=reporter)

    def route_user_input(self, user_input: UserQueryInput) -> tuple[ParsedQuery, ExecutionPlan]:
        self._emit(f"[router:start] {user_input.question or ''}")
        parsed_query = self.query_parser.parse(user_input)
        plan = self._build_plan_from_parsed_query(parsed_query, user_input.question or "")
        self._emit(f"[router:done] semantic plan -> {[skill.name for skill in plan.selected_skills]}")
        return parsed_query, plan

    def _build_plan_from_parsed_query(self, parsed_query: ParsedQuery, original_question: str) -> ExecutionPlan:
        if parsed_query.intent == "generate_reading_plan":
            find_args = {"entry_type": parsed_query.entry_type} if parsed_query.entry_type else {}
            plan = [
                SkillCall(name="summarize_repo", args={}),
                SkillCall(name="find_entrypoints", args=find_args),
                SkillCall(name="generate_reading_plan", args={"user_goal": parsed_query.user_goal or original_question}),
            ]
            return ExecutionPlan(intent=parsed_query.intent, selected_skills=plan, notes=parsed_query.notes)
        if parsed_query.intent == "find_entrypoints":
            args = {"entry_type": parsed_query.entry_type} if parsed_query.entry_type else {}
            return ExecutionPlan(intent=parsed_query.intent, selected_skills=[SkillCall(name="find_entrypoints", args=args)], notes=parsed_query.notes)
        if parsed_query.intent == "explain_module":
            args = {"module_path": parsed_query.module_path} if parsed_query.module_path else {}
            return ExecutionPlan(intent=parsed_query.intent, selected_skills=[SkillCall(name="explain_module", args=args)], notes=parsed_query.notes)
        if parsed_query.intent == "trace_symbol":
            args = {"symbol_name": parsed_query.symbol_name} if parsed_query.symbol_name else {}
            return ExecutionPlan(intent=parsed_query.intent, selected_skills=[SkillCall(name="trace_symbol", args=args)], notes=parsed_query.notes)
        return ExecutionPlan(intent="summarize_repo", selected_skills=[SkillCall(name="summarize_repo", args={})], notes=parsed_query.notes)

    def _emit(self, message: str) -> None:
        if self.reporter:
            self.reporter(message)
