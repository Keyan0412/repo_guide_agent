from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionAssistantMessageParam, ChatCompletionToolParam, ChatCompletionMessageToolCallParam
from dotenv import load_dotenv


class LLMClient:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = os.getenv("OPENAI_MODEL", "qwen-plus")
        self.enable_thinking = _parse_bool(os.getenv("ENABLE_THINKING"), default=False)
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800) -> str | None:
        if not self._client:
            return None
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_output_tokens,
            temperature=0.2,
            extra_body={"enable_thinking": self.enable_thinking},
        )
        return response.choices[0].message.content if response.choices else None

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200) -> dict[str, Any] | None:
        content = self.complete(system_prompt=system_prompt, user_prompt=user_prompt, max_output_tokens=max_output_tokens)
        if not content:
            return None
        return _extract_json_object(content)

    def run_tool_agent(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tools: list[ChatCompletionToolParam],
        tool_executor,
        progress_callback=None,
        max_iterations: int = 15,
        max_output_tokens: int = 1400,
    ) -> dict[str, Any] | None:
        if not self._client:
            return None
        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        for _ in range(max_iterations):
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=max_output_tokens,
                temperature=0.2,
                extra_body={"enable_thinking": self.enable_thinking},
            )
            if not response.choices:
                return None
            message = response.choices[0].message
            tool_calls = message.tool_calls or []
            if tool_calls:
                tool_call_params: list[ChatCompletionMessageToolCallParam] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ]
                assistant_message: ChatCompletionAssistantMessageParam = {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": tool_call_params,
                }
                messages.append(assistant_message)
                for tool_call in tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        arguments = {}
                    tool_result = tool_executor(tool_call.function.name, arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False),
                        }
                    )
                continue
            content = message.content or ""
            parsed = _extract_json_object(content)
            if parsed is not None:
                if progress_callback:
                    progress_callback("[llm] produced final JSON directly")
                return parsed
            messages.append({"role": "assistant", "content": content})
            break
        if progress_callback:
            progress_callback("[llm] forcing final JSON-only response")
        messages.append(
            {
                "role": "user",
                "content": "Return only the final JSON object now. No markdown, no explanation, no code fences.",
            }
        )
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_output_tokens,
            temperature=0.0,
            extra_body={"enable_thinking": self.enable_thinking},
        )
        if not response.choices:
            return None
        parsed = _extract_json_object(response.choices[0].message.content or "")
        if progress_callback:
            progress_callback("[llm] final JSON response received" if parsed is not None else "[llm] failed to return valid JSON")
        return parsed


def _extract_json_object(content: str) -> dict[str, Any] | None:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) >= 3:
            content = "\n".join(lines[1:-1]).strip()
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(content[start : end + 1])
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                return None
    return None


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
