from __future__ import annotations

import re
from typing import TextIO


class ProgressReporter:
    def __init__(self, stream: TextIO, verbose: bool = False) -> None:
        self.stream = stream
        self.verbose = verbose
        self._last_summary: str | None = None

    def __call__(self, message: str) -> None:
        rendered = message if self.verbose else self._summarize(message)
        if not rendered:
            return
        if not self.verbose and rendered == self._last_summary:
            return
        self._last_summary = rendered
        print(rendered, file=self.stream, flush=True)

    def _summarize(self, message: str) -> str | None:
        if message.startswith("[router:start]"):
            question = message[len("[router:start]") :].strip()
            return f"正在理解问题：{question}" if question else "正在理解问题"
        if message == "[query_parser] using llm semantic parser":
            return "正在分析问题意图并规划调查方向"
        if message == "[llm] waiting for semantic parse":
            return "正在生成调查计划"
        if message.startswith("[router:done]"):
            return "已确定调查流程，开始收集仓库线索"
        if message.startswith("[plan]"):
            return "准备按计划执行调查、整理和校验"
        if message.startswith("[workflow]") and "status=start" in message:
            return self._summarize_workflow_start(message)
        if message.startswith("[tool] "):
            return self._summarize_tool(message)
        if message.startswith("[tool:error]"):
            return "工具调用出现问题，正在调整调查路径"
        if message == "[executor:done] all skills completed":
            return "调查完成，正在生成最终回答"
        return None

    def _summarize_workflow_start(self, message: str) -> str | None:
        skill_match = re.search(r"name=([a-z_]+)", message)
        if not skill_match:
            return None
        skill_name = skill_match.group(1)
        if skill_name == "investigate_question":
            pass_match = re.search(r"node=investigate_pass_(\d+)", message)
            pass_index = pass_match.group(1) if pass_match else None
            if pass_index == "2":
                return "根据上一轮缺口继续补充调查"
            return "正在调查仓库结构和关键线索"
        if skill_name == "synthesize_answer":
            return "正在整理证据并起草回答"
        if skill_name == "verify_answer":
            return "正在检查回答是否完整且有证据支持"
        return None

    def _summarize_tool(self, message: str) -> str | None:
        if message.startswith("[tool] get_file_tree"):
            return "正在查看项目目录结构"
        if message.startswith("[tool] read_files"):
            count_match = re.search(r"'paths': \[(.*?)\]", message)
            if count_match:
                raw = count_match.group(1).strip()
                count = 0 if not raw else raw.count("', '") + 1
                if count <= 0:
                    count = 1
                return f"正在阅读 {count} 个关键文件"
            return "正在阅读关键文件"
        if message.startswith("[tool] search_keyword"):
            return "正在搜索仓库中的相关关键词"
        if message.startswith("[tool] search_symbol"):
            symbol_match = re.search(r"'symbol_name': '([^']+)'", message)
            if symbol_match:
                return f"正在追踪符号 `{symbol_match.group(1)}` 的定义和引用"
            return "正在追踪相关符号"
        return None
