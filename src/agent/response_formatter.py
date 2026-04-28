from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from src.agent.context import AgentContext
from src.errors import AgentError
from src.llm.client import LLMClient
from src.prompting import build_response_formatter_prompt
from src.schemas.skill_io import SkillOutput


class ResponseFormatter:
    def __init__(self, llm_client: LLMClient | None = None, output_dir: str = "outputs") -> None:
        self.llm_client = llm_client or LLMClient()
        self.output_dir = Path(output_dir)

    def format(self, outputs: list[SkillOutput], context: AgentContext, question: str | None = None) -> str:
        if not outputs:
            return "No skill output."
        output_path = self.save_raw_outputs(outputs, context, question=question)
        rendered = self._select_rendered_answer(outputs, context, question=question)
        if rendered is None:
            raise AgentError("response_formatter", f"LLM failed to render natural-language output. Raw JSON was saved to {output_path}.")
        return f"{rendered}\n\n结构化结果已保存到 `{output_path}`。"

    def save_raw_outputs(self, outputs: list[SkillOutput], context: AgentContext, question: str | None = None) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        payload = {
            "question": question,
            "repo_path": context.repo_path,
            "outputs": [output.model_dump() for output in outputs],
            "tool_logs": [tool_log.model_dump() for tool_log in context.tool_logs],
            "uncertainties": context.workflow_state.open_questions,
            "read_files": sorted(context.read_files),
            "workflow_state": asdict(context.workflow_state),
            "workflow_history": context.workflow_history,
        }
        file_path = self.output_dir / f"run_{timestamp}.json"
        file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(file_path)

    def _select_rendered_answer(self, outputs: list[SkillOutput], context: AgentContext, question: str | None = None) -> str | None:
        synthesized = None
        for output in reversed(outputs):
            answer = output.data.get("answer_markdown")
            if output.skill_name == "synthesize_answer" and isinstance(answer, str) and answer.strip():
                synthesized = answer.strip()
                break
        if synthesized and context.workflow_state.answer_ready:
            return synthesized
        return self._format_with_llm(outputs, context, question=question)

    def _format_with_llm(self, outputs: list[SkillOutput], context: AgentContext, question: str | None = None) -> str | None:
        if not self.llm_client.enabled:
            raise AgentError("response_formatter", "LLM client is unavailable for final answer rendering.")
        prompt = build_response_formatter_prompt(outputs, context, question=question)
        return self.llm_client.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=prompt.user_prompt,
            max_output_tokens=900,
        )
