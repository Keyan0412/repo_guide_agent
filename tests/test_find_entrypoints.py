from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput
from src.skills.find_entrypoints import FindEntrypointsSkill


class DummyLLMClient:
    enabled = True

    def run_tool_agent(self, **kwargs):
        return {
            "entry_candidates": [{"path": "src/main.py", "entry_type": "cli", "confidence": 0.9, "reason": "test", "supporting_evidence": []}],
            "recommended_first_read": ["src/main.py"],
            "uncertainties": [],
        }


def test_find_entrypoints_smoke():
    skill = FindEntrypointsSkill(llm_client=DummyLLMClient())
    output = skill.run(SkillInput(repo_path="."), AgentContext(repo_path="."))
    assert "entry_candidates" in output.data
