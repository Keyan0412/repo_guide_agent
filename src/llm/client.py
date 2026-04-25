from __future__ import annotations

import json
import os
from typing import Any, TypeVar

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolParam,
    ChatCompletionToolMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionMessageFunctionToolCall,
)
from dotenv import load_dotenv
from pydantic import BaseModel


ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMClient:
    def __init__(self) -> None:
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.model = os.getenv("OPENAI_MODEL", "qwen-plus")
        raw_enable_thinking = os.getenv("ENABLE_THINKING", "false").strip().lower()
        if raw_enable_thinking not in {"true", "false"}:
            raise ValueError("ENABLE_THINKING must be set to 'true' or 'false'.")
        self.enable_thinking = raw_enable_thinking == "true"
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def complete(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 800) -> str | None:
        """Return raw assistant text for a single system+user prompt pair."""
        if not self._client:
            return None

        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": system_prompt,
        }
        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": user_prompt,
        }
        messages: list[ChatCompletionMessageParam] = [system_message, user_message]

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_output_tokens,
            temperature=0.2,
            extra_body={"enable_thinking": self.enable_thinking},
        )
        return response.choices[0].message.content

    def generate_json(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 1200) -> dict[str, Any] | None:
        """Return the first JSON object parsed from a single completion response."""
        content = self.complete(system_prompt=system_prompt, user_prompt=user_prompt, max_output_tokens=max_output_tokens)
        if not content:
            return None
        return _extract_json_object(content)

    def generate_model(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[ModelT],
        max_output_tokens: int = 1200,
    ) -> ModelT | None:
        """Return a validated Pydantic model from a single completion response."""
        payload = self.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_output_tokens,
        )
        if payload is None:
            return None
        try:
            return schema.model_validate(payload)
        except Exception as exc:
            raise ValueError(
                f"LLM output failed validation for schema {schema.__name__}: {payload}"
            ) from exc

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
        """Run a tool-calling loop and return the final parsed JSON object."""
        if not self._client:
            return None
        system_message: ChatCompletionSystemMessageParam = {
            "role": "system",
            "content": system_prompt,
        }
        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": user_prompt,
        }
        messages: list[ChatCompletionMessageParam] = [system_message, user_message]

        for _ in range(max_iterations):

            # get model message
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
                raise RuntimeError("LLM tool-agent response contained no choices.")
            message = response.choices[0].message

            tool_calls = message.tool_calls or []
            if tool_calls:

                # add tool call information to messages
                tool_call_params: list[ChatCompletionMessageToolCallParam] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls if isinstance(tool_call, ChatCompletionMessageFunctionToolCall)
                ]
                assistant_message: ChatCompletionAssistantMessageParam = {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": tool_call_params,
                }
                messages.append(assistant_message)

                # execute tool calls and record
                for tool_call in tool_calls:
                    if not isinstance(tool_call, ChatCompletionMessageFunctionToolCall):
                        continue
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        arguments = {}
                    tool_result = tool_executor(tool_call.function.name, arguments)
                    tool_message: ChatCompletionToolMessageParam = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False),
                    }
                    messages.append(tool_message)
                continue

            # whether model returns final result
            content = message.content or ""
            parsed = _extract_json_object(content)
            if parsed is not None:
                if progress_callback:
                    progress_callback("[llm] produced final JSON directly")
                return parsed

            assistant_message: ChatCompletionAssistantMessageParam = {"role": "assistant", "content": content}
            messages.append(assistant_message)
            break

        # force final response
        if progress_callback:
            progress_callback("[llm] forcing final JSON-only response")
        user_message: ChatCompletionUserMessageParam = {
            "role": "user",
            "content": "Return only the final JSON object now. No markdown, no explanation, no code fences.",
        }
        messages.append(user_message)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_output_tokens,
            temperature=0.0,
            extra_body={"enable_thinking": self.enable_thinking},
        )
        if not response.choices:
            raise RuntimeError("LLM final JSON response contained no choices.")

        # parse final result
        final_content = response.choices[0].message.content or ""
        parsed = _extract_json_object(final_content)
        if parsed is None:
            raise ValueError(
                "LLM tool-agent failed to produce a valid final JSON object. "
                f"Final assistant output: {final_content}"
            )
        if progress_callback:
            progress_callback("[llm] final JSON response received")
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
