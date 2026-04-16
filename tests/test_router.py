from __future__ import annotations

from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 900):
        return self.payload


def test_route_builds_question_driven_workflow():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {
                "intent": "answer_repo_question",
                "objective": "execution_flow_explanation",
                "answer_mode": "ordered_steps",
                "module_path": None,
                "symbol_name": None,
                "user_goal": "解释处理流程",
                "entry_type": "cli",
                "key_entities": ["用户问题"],
                "required_evidence": ["entrypoint", "planning", "execution"],
                "investigation_focus": ["CLI 入口", "执行链路"],
                "expected_sections": ["整体结论", "步骤"],
                "confidence": 0.9,
                "notes": [],
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


def test_route_keeps_module_and_symbol_hints():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {
                "intent": "trace_symbol",
                "objective": "symbol_trace",
                "answer_mode": "call_chain",
                "module_path": None,
                "symbol_name": "train",
                "user_goal": None,
                "entry_type": None,
                "key_entities": ["train"],
                "required_evidence": ["symbol_definition", "symbol_references"],
                "investigation_focus": ["定义位置", "调用位置"],
                "expected_sections": ["结论", "调用链"],
                "confidence": 0.9,
                "notes": [],
            }
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed_query.symbol_name == "train"
    assert parsed_query.answer_mode == "call_chain"
    assert plan.selected_skills[0].name == "investigate_question"
