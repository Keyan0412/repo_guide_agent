from __future__ import annotations

from pathlib import Path

from src.agent.executor import Executor
from src.agent.response_formatter import ResponseFormatter
from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200):
        return {
            "intent": "generate_reading_plan",
            "module_path": None,
            "symbol_name": None,
            "user_goal": "理解启动链路",
            "entry_type": None,
            "confidence": 0.9,
            "notes": [],
        }

    def run_tool_agent(self, **kwargs):
        return {
            "user_goal": "理解启动链路",
            "reading_steps": [{"order": 1, "path": "src/main.py", "why_read": "入口", "focus_points": ["main"]}],
            "suggested_stop_condition": "stop",
            "uncertainties": [],
        }

    def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800):
        return "测试输出"


def test_ask_flow_has_bound_question(tmp_path):
    question = "如果我只想理解启动链路，应该按什么顺序读？"
    dummy = DummyLLMClient()
    user_input = UserQueryInput(repo_path=".", question=question)
    parsed_query, plan = Router(llm_client=dummy).route_user_input(user_input)
    context, outputs = Executor(llm_client=dummy).execute_plan(parsed_query, plan, verbose=False)
    rendered = ResponseFormatter(llm_client=dummy, output_dir=str(tmp_path)).format(
        outputs,
        context,
        question=question,
    )
    assert "结构化结果已保存到" in rendered
