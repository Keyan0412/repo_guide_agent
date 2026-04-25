from __future__ import annotations

from src.agent.executor import Executor
from src.agent.response_formatter import ResponseFormatter
from src.agent.router import Router
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self):
        self.json_payloads = [
            {
                "objective": "execution_flow_explanation",
                "answer_mode": "ordered_steps",
                "required_evidence": ["entrypoint", "planning", "execution", "output_rendering"],
                "investigation_focus": ["CLI 入口", "问题解析", "执行链路"],
            },
            {
                "answer_title": "任务流",
                "answer_markdown": "1. 解析命令行参数。\n2. 建模问题并调查仓库。\n3. 合成并校验答案。",
                "evidence": ["src/main.py", "src/agent/router.py", "src/agent/executor.py"],
                "coverage_points": ["说明了从输入到输出的步骤"],
                "remaining_gaps": [],
                "uncertainties": [],
            },
            {
                "verdict": "ready",
                "coverage_ok": True,
                "evidence": ["workflow_state 包含完整调查和回答结果"],
                "missing_points": [],
                "unsupported_claims": [],
                "recommended_focus": [],
                "uncertainties": [],
            },
        ]

    def generate_model(self, system_prompt: str, user_prompt: str, schema, max_output_tokens: int = 1200):
        return schema.model_validate(self.json_payloads.pop(0))

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200):
        return self.json_payloads.pop(0)

    def run_tool_agent(self, **kwargs):
        return {
            "investigation_summary": "找到入口、调查和输出链路。",
            "evidence": ["src/main.py", "src/agent/router.py", "src/agent/executor.py", "src/agent/response_formatter.py"],
            "findings": [{"claim": "主链路由 main、router、executor 和 formatter 组成。", "importance": "high", "evidence": ["src/main.py"], "related_files": ["src/main.py"]}],
            "evidence_gaps": [],
            "uncertainties": [],
        }

    def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800):
        return "测试输出"


def test_ask_flow_has_bound_question(tmp_path):
    question = "该项目在获得用户的问题后会经历怎样的过程来最终回答用户的问题？"
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
    assert context.workflow_state["completed_skills"] == [
        "investigate_question",
        "synthesize_answer",
        "verify_answer",
    ]
    assert context.workflow_state["answer_ready"] is True
    assert len(context.workflow_history) == 6
