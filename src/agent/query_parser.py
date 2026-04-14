from __future__ import annotations

import json
import re
from typing import Callable

from src.errors import AgentError
from src.llm.client import LLMClient
from src.schemas.response_models import ParsedQuery
from src.schemas.user_io import UserQueryInput
from src.utils.prompt_loader import render_prompt


class QueryParser:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        reporter: Callable[[str], None] | None = None,
    ) -> None:
        self.llm_client = llm_client or LLMClient()
        self.reporter = reporter

    def parse(self, user_input: UserQueryInput) -> ParsedQuery:
        self._emit(f"[query_parser:start] {user_input.question or ''}")
        if not self.llm_client.enabled:
            raise AgentError("query_parser", "LLM client is unavailable. Semantic parsing cannot continue.")
        self._emit("[query_parser] using llm semantic parser")
        parsed = self._parse_with_llm(user_input)
        if parsed is None:
            raise AgentError("query_parser", "LLM semantic parser failed to return valid ParsedQuery JSON.")
        parsed = parsed.model_copy(update={"repo_path": user_input.repo_path, "question": user_input.question})
        self._emit(f"[query_parser:done] llm intent={parsed.intent} symbol={parsed.symbol_name} module={parsed.module_path}")
        return parsed

    def _parse_with_llm(self, user_input: UserQueryInput) -> ParsedQuery | None:
        system_prompt = render_prompt(
            "prompts/system/query_parser.md",
            {
                "OUTPUT_SCHEMA": json.dumps(ParsedQuery.model_json_schema(), ensure_ascii=False, indent=2),
            },
        )
        user_prompt = json.dumps(
            {
                "question": user_input.question,
                "explicit_args": {
                    "module_path": None,
                    "symbol_name": None,
                    "entry_type": None,
                    "user_goal": None,
                },
            },
            ensure_ascii=False,
        )
        self._emit("[llm] waiting for semantic parse")
        result = self.llm_client.generate_json(system_prompt, user_prompt, max_output_tokens=900)
        if not result:
            return None
        try:
            return ParsedQuery.model_validate(result)
        except Exception:
            return None

    def _emit(self, message: str) -> None:
        if self.reporter:
            self.reporter(message)
