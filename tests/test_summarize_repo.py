from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput
from src.skills.summarize_repo import SummarizeRepoSkill


class DummyLLMClient:
    enabled = True

    def run_tool_agent(self, **kwargs):
        return {
            "repo_name": "repos_agent",
            "likely_purpose": "test",
            "primary_language": "Python",
            "frameworks": [],
            "project_type": "cli",
            "top_level_modules": [],
            "run_commands": [],
            "key_evidence": [],
            "uncertainties": [],
        }


def test_summarize_repo_smoke():
    skill = SummarizeRepoSkill(llm_client=DummyLLMClient())
    output = skill.run(SkillInput(repo_path="."), AgentContext(repo_path="."))
    assert output.data["repo_name"] == "repos_agent"
    assert "primary_language" in output.data
