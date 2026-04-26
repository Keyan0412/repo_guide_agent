from __future__ import annotations

from pathlib import Path

from src.tools.file_reader import read_files
from src.tools.file_tree import get_file_tree
from src.tools.keyword_search import search_keyword
from src.tools.symbol_search import search_symbol


def test_file_tree_smoke():
    result = get_file_tree(".", max_depth=2)
    assert "README.md" in result.tree_text
    assert result.file_count >= 1
    assert result.errors == []


def test_keyword_search_smoke():
    result = search_keyword(".", "Repo Guide Agent", top_k=5)
    assert result.hits
    assert all(hit.path for hit in result.hits)


def test_symbol_search_smoke():
    result = search_symbol(".", "main", "python", top_k=5)
    assert result.language == "python"
    assert result.supported is True
    assert isinstance(result.definitions, list)
    assert isinstance(result.references, list)
    assert isinstance(result.errors, list)
    assert all(hit.match_type for hit in result.definitions + result.references)


def test_keyword_search_reports_read_errors(tmp_path, monkeypatch):
    target = tmp_path / "broken.txt"
    target.write_text("match me\n", encoding="utf-8")
    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):
        if self.resolve() == target.resolve():
            raise PermissionError("blocked")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    result = search_keyword(str(tmp_path), "match", top_k=5)

    assert result.hits == []
    assert len(result.errors) == 1
    assert result.errors[0].path == "broken.txt"
    assert result.errors[0].operation == "read_text"


def test_symbol_search_reports_read_errors(tmp_path, monkeypatch):
    target = tmp_path / "broken.py"
    target.write_text("def main():\n    pass\n", encoding="utf-8")
    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args, **kwargs):
        if self.resolve() == target.resolve():
            raise PermissionError("blocked")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    result = search_symbol(str(tmp_path), "main", "python", top_k=5)

    assert result.definitions == []
    assert result.references == []
    assert len(result.errors) == 1
    assert result.errors[0].path == "broken.py"
    assert result.errors[0].operation == "read_text"


def test_symbol_search_reports_unsupported_language():
    result = search_symbol(".", "main", "go", top_k=5)

    assert result.language == "go"
    assert result.supported is False
    assert result.message == "Unsupported language: go"
    assert result.definitions == []
    assert result.references == []
    assert result.errors == []


def test_symbol_search_excludes_definition_lines_from_references(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        "def main():\n"
        "    return main_helper()\n"
        "\n"
        "def main_helper():\n"
        "    return 1\n"
        "\n"
        "main()\n",
        encoding="utf-8",
    )

    result = search_symbol(str(tmp_path), "main", "python", top_k=10)

    assert [(hit.path, hit.line) for hit in result.definitions] == [("sample.py", 1)]
    assert [(hit.path, hit.line, hit.match_type) for hit in result.references] == [
        ("sample.py", 7, "direct_identifier")
    ]


def test_symbol_search_classifies_reference_match_types(tmp_path):
    source = tmp_path / "sample.py"
    source.write_text(
        "import pkg.main as main_module\n"
        "main_module.main()\n"
        "x = main\n"
        "note = 'src/main.py'\n",
        encoding="utf-8",
    )

    result = search_symbol(str(tmp_path), "main", "python", top_k=10)

    assert [(hit.line, hit.match_type) for hit in result.references] == [
        (1, "module_or_alias"),
        (2, "module_or_alias"),
        (3, "direct_identifier"),
        (4, "path_or_text_mention"),
    ]


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
