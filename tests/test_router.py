from __future__ import annotations

from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self, payload):
        self.payload = payload

    def generate_model(self, system_prompt: str, user_prompt: str, schema, max_output_tokens: int = 900):
        return schema.model_validate(self.payload)


def test_route_builds_question_driven_workflow():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {
                "objective": "execution_flow_explanation",
                "answer_mode": "ordered_steps",
                "required_evidence": ["entrypoint", "planning", "execution"],
                "investigation_focus": ["CLI 入口", "执行链路"],
            }
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="系统如何处理用户问题？"))
    assert parsed_query.objective == "execution_flow_explanation"
    assert plan.intent == "execution_flow_explanation"
    assert plan.entry_node_id == "investigate_pass_1"
    assert [item.name for item in plan.selected_skills] == [
        "investigate_question",
        "synthesize_answer",
        "verify_answer",
        "investigate_question",
        "synthesize_answer",
        "verify_answer",
    ]
    assert any(edge.condition == "needs_followup" for edge in plan.edges)


def test_route_keeps_answer_mode_for_symbol_question():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {
                "objective": "symbol_trace",
                "answer_mode": "call_chain",
                "required_evidence": ["symbol_definition", "symbol_references"],
                "investigation_focus": ["定义位置", "调用位置"],
            }
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed_query.answer_mode == "call_chain"
    assert plan.selected_skills[0].name == "investigate_question"
