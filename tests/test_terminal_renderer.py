from __future__ import annotations

import io

from src.terminal_renderer import TerminalRenderer


class TTYBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


class PipeBuffer(io.StringIO):
    def isatty(self) -> bool:
        return False


def test_terminal_renderer_renders_rich_markdown_for_tty():
    renderer = TerminalRenderer()
    stream = TTYBuffer()

    renderer.render("# 标题\n\n1. `src/main.py`\n2. 第二项", stream=stream)

    output = stream.getvalue()
    assert "标题" in output
    assert "src/main.py" in output
    assert "# 标题" not in output
    assert "`src/main.py`" not in output


def test_terminal_renderer_falls_back_to_plain_text_for_non_tty():
    renderer = TerminalRenderer()
    stream = PipeBuffer()

    renderer.render("# 标题\n\n- `src/main.py`", stream=stream)

    output = stream.getvalue()
    assert "标题" in output
    assert "src/main.py" in output
    assert "# 标题" not in output
    assert "`src/main.py`" not in output
    assert output.endswith("\n")
