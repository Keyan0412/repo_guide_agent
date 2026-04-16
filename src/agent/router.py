from __future__ import annotations

from typing import Callable

from src.agent.query_parser import QueryParser
from src.llm.client import LLMClient
from src.schemas.response_models import ExecutionPlan, ParsedQuery, WorkflowEdge, WorkflowNode
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
        plan = self._build_plan_from_parsed_query(parsed_query)
        self._emit(f"[router:done] semantic plan -> {[skill.name for skill in plan.selected_skills]}")
        return parsed_query, plan

    def _build_plan_from_parsed_query(self, parsed_query: ParsedQuery) -> ExecutionPlan:
        nodes = [
            WorkflowNode(
                node_id="investigate_pass_1",
                node_type="skill",
                name="investigate_question",
                args={"pass_index": 1},
            ),
            WorkflowNode(
                node_id="synthesize_pass_1",
                node_type="skill",
                name="synthesize_answer",
                args={"pass_index": 1},
            ),
            WorkflowNode(
                node_id="verify_pass_1",
                node_type="skill",
                name="verify_answer",
                args={"pass_index": 1},
            ),
            WorkflowNode(
                node_id="investigate_pass_2",
                node_type="skill",
                name="investigate_question",
                args={"pass_index": 2, "focus_source": "verifier_feedback"},
            ),
            WorkflowNode(
                node_id="synthesize_pass_2",
                node_type="skill",
                name="synthesize_answer",
                args={"pass_index": 2},
            ),
            WorkflowNode(
                node_id="verify_pass_2",
                node_type="skill",
                name="verify_answer",
                args={"pass_index": 2},
            ),
        ]
        edges = [
            WorkflowEdge(source="investigate_pass_1", target="synthesize_pass_1"),
            WorkflowEdge(source="synthesize_pass_1", target="verify_pass_1"),
            WorkflowEdge(source="verify_pass_1", target="investigate_pass_2", condition="needs_followup"),
            WorkflowEdge(source="investigate_pass_2", target="synthesize_pass_2"),
            WorkflowEdge(source="synthesize_pass_2", target="verify_pass_2"),
        ]
        return ExecutionPlan(
            intent=parsed_query.objective,
            entry_node_id="investigate_pass_1",
            nodes=nodes,
            edges=edges,
            notes=parsed_query.notes,
        )

    def _emit(self, message: str) -> None:
        if self.reporter:
            self.reporter(message)
