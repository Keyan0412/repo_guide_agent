from __future__ import annotations

from src.agent.executor import Executor
from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self):
        self.json_payloads = [
            {
                "intent": "answer_repo_question",
                "objective": "repo_overview",
                "answer_mode": "direct_answer",
                "module_path": None,
                "symbol_name": None,
                "user_goal": None,
                "entry_type": None,
                "key_entities": ["仓库"],
                "required_evidence": ["repo_structure", "entrypoint"],
                "investigation_focus": ["顶层结构", "入口"],
                "expected_sections": ["结论", "证据"],
                "confidence": 0.9,
                "notes": [],
            },
            {
                "answer_title": None,
                "answer_markdown": "这是一个测试仓库回答。",
                "coverage_points": ["概述了仓库用途"],
                "remaining_gaps": [],
                "uncertainties": [],
            },
            {
                "verdict": "ready",
                "coverage_ok": True,
                "missing_points": [],
                "unsupported_claims": [],
                "recommended_focus": [],
                "uncertainties": [],
            },
        ]

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200):
        return self.json_payloads.pop(0)

    def run_tool_agent(self, **kwargs):
        return {
            "investigation_summary": "定位到入口和顶层结构。",
            "findings": [{"claim": "仓库提供命令行入口。", "importance": "high", "evidence": ["src/main.py"], "related_files": ["src/main.py"]}],
            "evidence_gaps": [],
            "uncertainties": [],
        }


def test_verbose_execution_emits_progress():
    messages: list[str] = []
    reporter = messages.append
    dummy = DummyLLMClient()
    router = Router(llm_client=dummy, reporter=reporter)
    parsed_query, plan = router.route_user_input(UserQueryInput(repo_path=".", question="这个仓库是干什么的？"))
    executor = Executor(llm_client=dummy, reporter=reporter)
    context, outputs = executor.execute_plan(parsed_query, plan, verbose=True)
    assert outputs
    assert any(message.startswith("[router:start]") for message in messages)
    assert any(message.startswith("[skill:start] investigate_question") for message in messages)
    assert any(message.startswith("[query_parser:start]") for message in messages)
    assert any(message.startswith("[workflow] node=investigate_pass_1") for message in messages)
    assert context.workflow_state["completed_skills"] == [
        "investigate_question",
        "synthesize_answer",
        "verify_answer",
    ]
    assert context.workflow_state["answer_ready"] is True
    assert context.workflow_state["draft_answer"] == "这是一个测试仓库回答。"
