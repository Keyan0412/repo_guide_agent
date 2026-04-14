from __future__ import annotations

from src.agent.executor import Executor
from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200):
        return {
            "intent": "summarize_repo",
            "module_path": None,
            "symbol_name": None,
            "user_goal": None,
            "entry_type": None,
            "confidence": 0.9,
            "notes": [],
        }

    def run_tool_agent(self, **kwargs):
        return {
            "repo_name": "repos_agent",
            "likely_purpose": "测试",
            "primary_language": "Python",
            "frameworks": [],
            "project_type": "cli",
            "top_level_modules": [],
            "run_commands": [],
            "key_evidence": [],
            "uncertainties": [],
        }


def test_verbose_execution_emits_progress():
    messages: list[str] = []
    reporter = messages.append
    dummy = DummyLLMClient()
    router = Router(llm_client=dummy, reporter=reporter)
    parsed_query, plan = router.route_user_input(UserQueryInput(repo_path=".", question="这个仓库是干什么的？"))
    executor = Executor(llm_client=dummy, reporter=reporter)
    _, outputs = executor.execute_plan(parsed_query, plan, verbose=True)
    assert outputs
    assert any(message.startswith("[router:start]") for message in messages)
    assert any(message.startswith("[skill:start] summarize_repo") for message in messages)
    assert any(message.startswith("[query_parser:start]") for message in messages)
