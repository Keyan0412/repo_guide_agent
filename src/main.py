from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.agent.executor import Executor
from src.agent.response_formatter import ResponseFormatter
from src.agent.router import Router
from src.errors import AgentError
from src.llm.client import LLMClient
from src.progress_reporter import ProgressReporter
from src.schemas.user_io import UserQueryInput
from src.terminal_renderer import TerminalRenderer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repo Guide Agent")
    parser.add_argument("--verbose", action="store_true", help="Print intermediate router/skill/tool progress to stderr.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--question", required=True, help="Natural-language question about the repository.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    reporter = ProgressReporter(stream=sys.stderr, verbose=args.verbose)
    llm_client = LLMClient()
    renderer = TerminalRenderer()
    executor = Executor(llm_client=llm_client, reporter=reporter)
    formatter = ResponseFormatter(llm_client=llm_client)
    router = Router(llm_client=llm_client, reporter=reporter)
    try:
        question = args.question
        user_input = UserQueryInput(repo_path=str(Path(args.repo).resolve()), question=question)
        parsed_query, plan = router.route_user_input(user_input)

        reporter(f"[plan] intent={plan.intent} skills={[skill.name for skill in plan.selected_skills]}")
        context, outputs = executor.execute_plan(parsed_query, plan, verbose=args.verbose, show_progress=True)
        renderer.render(formatter.format(outputs, context, question=question), stream=sys.stdout)
    except AgentError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
