from __future__ import annotations

from src.agent.query_parser import QueryParser
from src.schemas.user_io import UserQueryInput


class DummyLLMClient:
    enabled = True

    def __init__(self, payload):
        self.payload = payload

    def generate_model(self, system_prompt: str, user_prompt: str, schema, max_output_tokens: int = 900):
        return schema.model_validate(self.payload)

def test_llm_query_parser_models_module_question():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "objective": "module_explanation",
                "answer_mode": "direct_answer",
                "required_evidence": ["module_role"],
                "investigation_focus": ["目录结构", "关键文件"],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="解释一下 src/retriever 目录是做什么的。"))
    assert parsed.objective == "module_explanation"


def test_llm_query_parser_models_symbol_question():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "objective": "symbol_trace",
                "answer_mode": "call_chain",
                "required_evidence": ["symbol_definition", "symbol_references"],
                "investigation_focus": ["定义位置", "调用位置"],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="train() 最终是从哪里被调用起来的？"))
    assert parsed.answer_mode == "call_chain"


def test_llm_query_parser_models_flow_question():
    parser = QueryParser(
        llm_client=DummyLLMClient(
            {
                "objective": "execution_flow_explanation",
                "answer_mode": "ordered_steps",
                "required_evidence": ["entrypoint", "planning", "execution", "output_rendering"],
                "investigation_focus": ["入口", "调度", "格式化"],
            }
        ),
    )
    parsed = parser.parse(UserQueryInput(repo_path=".", question="系统如何处理用户问题并生成最终回答？"))
    assert parsed.objective == "execution_flow_explanation"
    assert parsed.answer_mode == "ordered_steps"
