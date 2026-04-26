from __future__ import annotations

from pathlib import Path

from src.tools.repo_walk import RepoWalkEntry, RepoWalkError, iter_repo_entries


def _build_repo(root: Path) -> None:
    (root / "app").mkdir()
    (root / "app" / "nested").mkdir()
    (root / "node_modules").mkdir()
    (root / ".git").mkdir()
    (root / "z-last.txt").write_text("z\n", encoding="utf-8")
    (root / "a-first.py").write_text("print('a')\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (root / "image.png").write_text("not really binary\n", encoding="utf-8")
    (root / "app" / "main.py").write_text("def main():\n    pass\n", encoding="utf-8")
    (root / "app" / "nested" / "deep.py").write_text("DEEP = True\n", encoding="utf-8")
    (root / "node_modules" / "ignored.js").write_text("ignored\n", encoding="utf-8")
    (root / ".git" / "config").write_text("[core]\n", encoding="utf-8")


def test_iter_repo_entries_keeps_stable_order(tmp_path: Path):
    _build_repo(tmp_path)

    entries = [
        event.path.relative_to(tmp_path).as_posix()
        for event in iter_repo_entries(tmp_path)
        if isinstance(event, RepoWalkEntry)
    ]

    assert entries == [
        ".git",
        ".git/config",
        "app",
        "app/nested",
        "app/nested/deep.py",
        "app/main.py",
        "node_modules",
        "node_modules/ignored.js",
        ".env",
        "a-first.py",
        "image.png",
        "z-last.txt",
    ]


def test_iter_repo_entries_files_only_and_max_depth(tmp_path: Path):
    _build_repo(tmp_path)

    entries = [
        path.relative_to(tmp_path).as_posix()
        for event in iter_repo_entries(tmp_path, files_only=True, max_depth=1)
        if isinstance(event, RepoWalkEntry)
        for path in [event.path]
    ]

    assert entries == [
        ".env",
        "a-first.py",
        "image.png",
        "z-last.txt",
    ]


def test_iter_repo_entries_respects_start_path(tmp_path: Path):
    _build_repo(tmp_path)

    entries = [
        path.relative_to(tmp_path).as_posix()
        for event in iter_repo_entries(tmp_path / "app", files_only=True)
        if isinstance(event, RepoWalkEntry)
        for path in [event.path]
    ]

    assert entries == [
        "app/nested/deep.py",
        "app/main.py",
    ]


def test_iter_repo_entries_reports_directory_errors(tmp_path: Path, monkeypatch):
    _build_repo(tmp_path)
    blocked = (tmp_path / "app" / "nested").resolve()
    original_iterdir = Path.iterdir

    def fake_iterdir(self: Path):
        if self.resolve() == blocked:
            raise PermissionError("blocked")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", fake_iterdir)

    errors = [
        event
        for event in iter_repo_entries(tmp_path)
        if isinstance(event, RepoWalkError)
    ]

    assert len(errors) == 1
    assert errors[0].path == str(blocked)
    assert errors[0].operation == "iterdir"
    assert errors[0].error_type == "PermissionError"
