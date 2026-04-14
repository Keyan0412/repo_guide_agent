from __future__ import annotations

from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 900):
        return self.payload


def test_route_summary():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {"intent": "summarize_repo", "module_path": None, "symbol_name": None, "user_goal": None, "entry_type": None, "confidence": 0.9, "notes": []}
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="这个仓库是干什么的？"))
    assert parsed_query.intent == "summarize_repo"
    assert plan.selected_skills[0].name == "summarize_repo"


def test_route_trace():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {"intent": "trace_symbol", "module_path": None, "symbol_name": "train", "user_goal": None, "entry_type": None, "confidence": 0.9, "notes": []}
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed_query.intent == "trace_symbol"
    assert plan.selected_skills[0].name == "trace_symbol"


def test_route_reading_plan_priority():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {"intent": "generate_reading_plan", "module_path": None, "symbol_name": None, "user_goal": "帮我理解这个仓库的训练流程，从入口开始说明。", "entry_type": "training", "confidence": 0.9, "notes": []}
        ),
    ).route_user_input(UserQueryInput(repo_path=".", question="帮我理解这个仓库的训练流程，从入口开始说明。"))
    assert parsed_query.intent == "generate_reading_plan"
    assert [item.name for item in plan.selected_skills] == [
        "summarize_repo",
        "find_entrypoints",
        "generate_reading_plan",
    ]


def test_route_module_explanation_uses_semantic_slots():
    parsed_query, plan = Router(
        llm_client=DummyLLMClient(
            {"intent": "explain_module", "module_path": "src/retriever", "symbol_name": None, "user_goal": None, "entry_type": None, "confidence": 0.9, "notes": []}
        ),
    ).route_user_input(
        UserQueryInput(repo_path=".", question="解释一下 src/retriever 目录是做什么的。")
    )
    assert parsed_query.module_path == "src/retriever"
    assert plan.selected_skills[0].args["module_path"] == "src/retriever"
