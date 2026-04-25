from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput
from src.skills.trace_symbol import TraceSymbolSkill


class DummyLLMClient:
    enabled = True

    def run_tool_agent(self, **kwargs):
        return {
            "symbol_name": "main",
            "evidence": ["src/main.py:1 def main()"],
            "definitions": [{"path": "src/main.py", "line": 1, "signature": "def main()"}],
            "references": [],
            "most_likely_call_chain": [],
            "conclusion": "test",
            "uncertainties": [],
        }


def test_trace_symbol_smoke():
    skill = TraceSymbolSkill(llm_client=DummyLLMClient())
    output = skill.run(SkillInput(repo_path=".", question="main() 在哪里定义？"), AgentContext(repo_path="."))
    assert output.data["symbol_name"] == "main"
