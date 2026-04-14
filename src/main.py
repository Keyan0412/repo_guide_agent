from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.agent.executor import Executor
from src.agent.response_formatter import ResponseFormatter
from src.agent.router import Router
from src.errors import AgentError
from src.llm.client import LLMClient
from src.schemas.user_io import UserQueryInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Repo Guide Agent")
    parser.add_argument("--verbose", action="store_true", help="Print intermediate router/skill/tool progress to stderr.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--question", required=True, help="Natural-language question about the repository.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    reporter = _stderr_reporter if args.verbose else None
    llm_client = LLMClient()
    executor = Executor(llm_client=llm_client, reporter=reporter)
    formatter = ResponseFormatter(llm_client=llm_client)
    router = Router(llm_client=llm_client, reporter=reporter)
    try:
        question = args.question
        user_input = UserQueryInput(repo_path=str(Path(args.repo).resolve()), question=question)
        parsed_query, plan = router.route_user_input(user_input)

        if reporter:
            reporter(f"[plan] intent={plan.intent} skills={[skill.name for skill in plan.selected_skills]}")
        context, outputs = executor.execute_plan(parsed_query, plan, verbose=args.verbose)
        print(formatter.format(outputs, context, question=question))
    except AgentError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        sys.exit(1)


def _stderr_reporter(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
