from __future__ import annotations

from src.agent.executor import Executor
from src.agent.context import AgentContext
from src.agent.router import Router
from src.schemas.user_io import UserQueryInput
from src.schemas.skill_io import SkillInput
from src.skills.investigate_question import InvestigateQuestionSkill


class DummyLLMClient:
    enabled = True

    def __init__(self):
        self.json_payloads = [
            {
                "objective": "repo_overview",
                "answer_mode": "direct_answer",
                "required_evidence": ["repo_structure", "entrypoint"],
                "investigation_focus": ["顶层结构", "入口"],
            },
            {
                "answer_title": None,
                "answer_markdown": "这是一个测试仓库回答。",
                "evidence": ["README.md", "src/main.py"],
                "coverage_points": ["概述了仓库用途"],
                "remaining_gaps": [],
                "uncertainties": [],
            },
            {
                "verdict": "ready",
                "coverage_ok": True,
                "evidence": ["调查结果已经覆盖仓库用途与入口"],
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
            "investigation_summary": "定位到入口和顶层结构。",
            "evidence": ["src/main.py"],
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


class DummyInvestigateLLMClient:
    enabled = True

    def run_tool_agent(self, **kwargs):
        return {
            "investigation_summary": "收集了仓库线索。",
            "evidence": ["bootstrap", "src/main.py"],
            "findings": [
                {
                    "claim": "调查阶段已经读取了项目树和代码文件。",
                    "importance": "high",
                    "evidence": ["bootstrap"],
                    "related_files": ["bootstrap"],
                }
            ],
            "evidence_gaps": [],
            "uncertainties": [],
        }


def test_investigate_bootstraps_tree_without_preselected_files(tmp_path):
    repo = tmp_path / "repo"
    src_dir = repo / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
    (src_dir / "service.py").write_text("SERVICE_NAME = 'mentor-finder'\n", encoding="utf-8")
    (repo / "docs").mkdir()

    context = AgentContext(repo_path=str(repo))
    skill = InvestigateQuestionSkill(llm_client=DummyInvestigateLLMClient())
    output = skill.run(
        SkillInput(repo_path=str(repo), question="这个仓库是干什么的？", objective="repo_overview"),
        context,
    )

    assert output.skill_name == "investigate_question"
    assert any(log.tool_name == "get_file_tree" for log in context.tool_logs)
    assert not any(log.tool_name == "read_files" for log in context.tool_logs)
    assert not context.read_files
