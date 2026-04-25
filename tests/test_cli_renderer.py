from __future__ import annotations

import io

import src.main as main_module


class DummyStdout(io.StringIO):
    def __init__(self, is_tty: bool):
        super().__init__()
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


class DummyParser:
    def parse_args(self):
        return type("Args", (), {"verbose": False, "repo": ".", "question": "入口在哪里？"})()


class DummyRouter:
    def __init__(self, llm_client=None, reporter=None):
        self.llm_client = llm_client

    def route_user_input(self, user_input):
        return "parsed-query", type("Plan", (), {"intent": "answer", "selected_skills": []})()


class DummyExecutor:
    def __init__(self, llm_client=None, reporter=None):
        self.llm_client = llm_client

    def execute_plan(self, parsed_query, plan, verbose=False, show_progress=False):
        return "context", ["output"]


class DummyFormatter:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    def format(self, outputs, context, question=None):
        return "# 标题\n\n1. `src/main.py`"


class DummyRenderer:
    def __init__(self):
        self.calls = []

    def render(self, text, stream):
        self.calls.append((text, stream))


def test_main_routes_output_through_terminal_renderer(monkeypatch):
    renderer = DummyRenderer()
    stdout = DummyStdout(is_tty=True)
    stderr = io.StringIO()

    monkeypatch.setattr(main_module, "build_parser", lambda: DummyParser())
    monkeypatch.setattr(main_module, "LLMClient", lambda: object())
    monkeypatch.setattr(main_module, "Router", DummyRouter)
    monkeypatch.setattr(main_module, "Executor", DummyExecutor)
    monkeypatch.setattr(main_module, "ResponseFormatter", DummyFormatter)
    monkeypatch.setattr(main_module, "TerminalRenderer", lambda: renderer)
    monkeypatch.setattr(main_module.sys, "stdout", stdout)
    monkeypatch.setattr(main_module.sys, "stderr", stderr)

    main_module.main()

    assert renderer.calls == [("# 标题\n\n1. `src/main.py`", stdout)]
    assert "准备按计划执行调查、整理和校验" in stderr.getvalue()
