from __future__ import annotations

import io

from src.progress_reporter import ProgressReporter


def test_progress_reporter_summarizes_default_messages():
    stream = io.StringIO()
    reporter = ProgressReporter(stream=stream, verbose=False)

    reporter("[router:start] 这个仓库是干什么的？")
    reporter("[tool] get_file_tree {'path': '/tmp/repo', 'max_depth': 3}")
    reporter("[tool] read_files {'paths': ['README.md', 'src/main.py'], 'start_line': 1, 'end_line': 220}")
    reporter("[executor:done] all skills completed")

    output = stream.getvalue()
    assert "正在理解问题：这个仓库是干什么的？" in output
    assert "正在查看项目目录结构" in output
    assert "正在阅读 2 个关键文件" in output
    assert "调查完成，正在生成最终回答" in output


def test_progress_reporter_keeps_raw_messages_in_verbose_mode():
    stream = io.StringIO()
    reporter = ProgressReporter(stream=stream, verbose=True)

    reporter("[tool] get_file_tree {'path': '/tmp/repo', 'max_depth': 3}")

    assert stream.getvalue() == "[tool] get_file_tree {'path': '/tmp/repo', 'max_depth': 3}\n"
