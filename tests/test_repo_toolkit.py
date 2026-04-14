from __future__ import annotations

from src.agent.context import AgentContext
from src.tools.repo_toolkit import RepoToolkit, build_tool_schemas


def test_tool_schemas_smoke():
    tools = build_tool_schemas()
    names = [tool["function"]["name"] for tool in tools]
    assert names == ["get_file_tree", "read_files", "search_keyword", "search_symbol"]


def test_repo_toolkit_executes_keyword_search():
    toolkit = RepoToolkit(".", AgentContext(repo_path="."))
    result = toolkit.execute("search_keyword", {"query": "项目说明书", "top_k": 3})
    assert result["hits"]


def test_repo_toolkit_executes_read_files():
    toolkit = RepoToolkit(".", AgentContext(repo_path="."))
    result = toolkit.execute(
        "read_files",
        {
            "paths": ["README.md", "pyproject.toml"],
            "start_line": 1,
            "end_line": 5,
        },
    )
    assert len(result["files"]) == 2
    assert result["files"][0]["path"].endswith("README.md")
    assert result["files"][1]["path"].endswith("pyproject.toml")


def test_repo_toolkit_executes_read_files_with_single_path():
    toolkit = RepoToolkit(".", AgentContext(repo_path="."))
    result = toolkit.execute(
        "read_files",
        {
            "paths": ["README.md"],
            "start_line": 1,
            "end_line": 5,
        },
    )
    assert len(result["files"]) == 1
    assert result["files"][0]["path"].endswith("README.md")


def test_repo_toolkit_executes_read_files_with_partial_failure():
    toolkit = RepoToolkit(".", AgentContext(repo_path="."))
    result = toolkit.execute(
        "read_files",
        {
            "paths": ["README.md", "src/tools"],
            "start_line": 1,
            "end_line": 5,
        },
    )
    assert len(result["files"]) == 1
    assert result["files"][0]["path"].endswith("README.md")
    assert len(result["errors"]) == 1
    assert result["errors"][0]["path"].endswith("src/tools")
    assert "IsADirectoryError" in result["errors"][0]["error"]
