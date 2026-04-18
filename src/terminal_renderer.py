from __future__ import annotations

import io
from typing import TextIO

from rich.console import Console
from rich.markdown import Markdown


class TerminalRenderer:
    def render(self, text: str, stream: TextIO) -> None:
        if self._should_render_markdown(stream):
            Console(file=stream, force_terminal=True, color_system="auto", soft_wrap=True).print(Markdown(text))
            return
        stream.write(self.render_plain_text(text))
        if not text.endswith("\n"):
            stream.write("\n")

    @staticmethod
    def render_plain_text(text: str) -> str:
        buffer = io.StringIO()
        Console(file=buffer, force_terminal=False, color_system=None, soft_wrap=True).print(Markdown(text))
        return buffer.getvalue().rstrip("\n")

    @staticmethod
    def _should_render_markdown(stream: TextIO) -> bool:
        isatty = getattr(stream, "isatty", None)
        return bool(callable(isatty) and isatty())
