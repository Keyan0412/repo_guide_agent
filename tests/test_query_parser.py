from __future__ import annotations

from src.agent.query_parser import QueryParser
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 900):
        return self.payload


def test_llm_query_parser_extracts_module_path():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "intent": "explain_module",
                "module_path": "src/retriever",
                "symbol_name": None,
                "user_goal": None,
                "entry_type": None,
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="解释一下 src/retriever 目录是做什么的。"))
    assert parsed.module_path == "src/retriever"


def test_llm_query_parser_extracts_symbol():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "intent": "trace_symbol",
                "module_path": None,
                "symbol_name": "train",
                "user_goal": None,
                "entry_type": None,
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed.symbol_name == "train"


def test_llm_query_parser_infers_reading_plan():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "intent": "generate_reading_plan",
                "module_path": None,
                "symbol_name": None,
                "user_goal": "如果我只想理解启动链路，应该按什么顺序读？",
                "entry_type": "cli",
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="如果我只想理解启动链路，应该按什么顺序读？"))
    assert parsed.intent == "generate_reading_plan"
