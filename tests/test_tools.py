from __future__ import annotations

from src.tools.file_reader import read_files
from src.tools.file_tree import get_file_tree
from src.tools.keyword_search import search_keyword
from src.tools.symbol_search import search_symbol


def test_file_tree_smoke():
    result = get_file_tree(".", max_depth=2)
    assert "repo_guide_agent_project_spec.md" in result.tree_text
    assert result.file_count >= 1


def test_keyword_search_smoke():
    hits = search_keyword(".", "项目说明书", top_k=5)
    assert hits
    assert hits[0].path.endswith("repo_guide_agent_project_spec.md")


def test_symbol_search_smoke():
    hits = search_symbol(".", "main", top_k=5)
    assert "definitions" in hits
    assert "references" in hits


def test_read_files_smoke():
    result = read_files(["README.md", "pyproject.toml"], start_line=1, end_line=3)
    assert len(result.files) == 2
    assert result.files[0].path.endswith("README.md")
    assert result.files[1].path.endswith("pyproject.toml")


def test_read_files_single_path_smoke():
    result = read_files(["README.md"], start_line=1, end_line=3)
    assert len(result.files) == 1
    assert result.files[0].path.endswith("README.md")


def test_read_files_tolerates_invalid_path():
    result = read_files(["README.md", "src/tools"], start_line=1, end_line=3)
    assert len(result.files) == 1
    assert result.files[0].path.endswith("README.md")
    assert len(result.errors) == 1
    assert result.errors[0].path.endswith("src/tools")
    assert "IsADirectoryError" in result.errors[0].error
