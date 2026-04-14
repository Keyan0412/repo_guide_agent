from __future__ import annotations

from pathlib import Path

import pytest

from src.agent.context import AgentContext
from src.errors import AgentError
from src.agent.response_formatter import ResponseFormatter
from src.schemas.skill_io import SkillOutput


class DummyLLMClient:
    enabled = True

    def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800):
        return "测试用自然语言输出"


def test_response_formatter_saves_json_output(tmp_path: Path):
    formatter = ResponseFormatter(llm_client=DummyLLMClient(), output_dir=str(tmp_path))
    context = AgentContext(repo_path=".")
    outputs = [
        SkillOutput(
            skill_name="summarize_repo",
            data={
                "likely_purpose": "用于快速理解陌生代码仓库",
                "primary_language": "Python",
                "project_type": "cli",
                "top_level_modules": [{"path": "src/"}, {"path": "tests/"}],
                "frameworks": ["Pydantic"],
                "run_commands": ["repo-guide-agent summarize --repo /tmp/demo"],
                "uncertainties": [],
            },
        )
    ]
    rendered = formatter.format(outputs, context, question="这个仓库是干什么的？")
    assert "结构化结果已保存到" in rendered
    saved = list(tmp_path.glob("run_*.json"))
    assert len(saved) == 1


def test_response_formatter_errors_without_llm(tmp_path: Path):
    class BrokenLLMClient:
        enabled = False

        def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800):
            return None

    formatter = ResponseFormatter(llm_client=BrokenLLMClient(), output_dir=str(tmp_path))
    context = AgentContext(repo_path=".")
    outputs = [
        SkillOutput(
            skill_name="find_entrypoints",
            data={
                "entry_candidates": [
                    {"path": "src/main.py", "entry_type": "cli", "reason": "包含 main 和 argparse"}
                ],
                "uncertainties": [],
            },
        )
    ]
    with pytest.raises(AgentError):
        formatter.format(outputs, context, question="入口在哪里？")
