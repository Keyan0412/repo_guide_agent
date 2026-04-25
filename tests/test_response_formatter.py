from __future__ import annotations

from pathlib import Path

import pytest
import json

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
            skill_name="investigate_question",
            data={
                "investigation_summary": "定位到仓库用途与主入口。",
                "evidence": ["README.md", "src/main.py"],
                "findings": [
                    {
                        "claim": "这是一个用于理解代码仓库的命令行 Agent。",
                        "importance": "high",
                        "evidence": ["README.md", "src/main.py"],
                        "related_files": ["README.md", "src/main.py"],
                    }
                ],
                "evidence_gaps": [],
                "uncertainties": [],
            },
        )
    ]
    rendered = formatter.format(outputs, context, question="这个仓库是干什么的？")
    assert "结构化结果已保存到" in rendered
    saved = list(tmp_path.glob("run_*.json"))
    assert len(saved) == 1
    payload = json.loads(saved[0].read_text(encoding="utf-8"))
    assert "workflow_state" in payload
    assert "workflow_history" in payload


def test_response_formatter_errors_without_llm(tmp_path: Path):
    class BrokenLLMClient:
        enabled = False

        def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800):
            return None

    formatter = ResponseFormatter(llm_client=BrokenLLMClient(), output_dir=str(tmp_path))
    context = AgentContext(repo_path=".")
    outputs = [
        SkillOutput(
            skill_name="investigate_question",
            data={
                "investigation_summary": "已定位入口候选。",
                "evidence": ["src/main.py"],
                "findings": [],
                "evidence_gaps": [],
                "uncertainties": [],
            },
        )
    ]
    with pytest.raises(AgentError):
        formatter.format(outputs, context, question="入口在哪里？")
