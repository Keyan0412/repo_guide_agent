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
                "objective": "module_explanation",
                "answer_mode": "module_explanation",
                "module_path": "src/retriever",
                "symbol_name": None,
                "user_goal": None,
                "entry_type": None,
                "key_entities": ["src/retriever"],
                "required_evidence": ["module_role"],
                "investigation_focus": ["目录结构", "关键文件"],
                "expected_sections": ["模块职责", "关键文件"],
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="解释一下 src/retriever 目录是做什么的。"))
    assert parsed.module_path == "src/retriever"
    assert parsed.objective == "module_explanation"


def test_llm_query_parser_extracts_symbol():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "intent": "trace_symbol",
                "objective": "symbol_trace",
                "answer_mode": "call_chain",
                "module_path": None,
                "symbol_name": "train",
                "user_goal": None,
                "entry_type": None,
                "key_entities": ["train"],
                "required_evidence": ["symbol_definition", "symbol_references"],
                "investigation_focus": ["定义位置", "调用位置"],
                "expected_sections": ["结论", "调用链"],
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed.symbol_name == "train"
    assert parsed.answer_mode == "call_chain"


def test_llm_query_parser_models_flow_question():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "intent": "answer_repo_question",
                "objective": "execution_flow_explanation",
                "answer_mode": "ordered_steps",
                "module_path": None,
                "symbol_name": None,
                "user_goal": "解释从用户问题到最终回答的处理流程",
                "entry_type": "cli",
                "key_entities": ["用户问题", "最终回答"],
                "required_evidence": ["entrypoint", "planning", "execution", "output_rendering"],
                "investigation_focus": ["入口", "调度", "格式化"],
                "expected_sections": ["整体结论", "步骤"],
                "confidence": 0.9,
                "notes": [],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="系统如何处理用户问题并生成最终回答？"))
    assert parsed.objective == "execution_flow_explanation"
    assert parsed.answer_mode == "ordered_steps"
