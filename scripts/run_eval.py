from __future__ import annotations

from src.agent.executor import Executor
from src.agent.router import Router
from src.schemas.skill_io import SkillInput


def run_case(repo: str, question: str) -> None:
    plan = Router().route(question)
    context, outputs = Executor().execute_plan(SkillInput(repo_path=repo, question=question), plan)
    print(question)
    print(outputs[-1].data)
    print(len(context.tool_logs))


if __name__ == "__main__":
    run_case(".", "这个仓库是干什么的？")
