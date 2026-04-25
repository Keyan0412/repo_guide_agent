from __future__ import annotations

from pathlib import Path
from typing import Any

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput
from src.skills.base import BaseSkill
from src.tools.path_filter import should_ignore
from src.tools.repo_toolkit import RepoToolkit


class InvestigateQuestionSkill(BaseSkill):
    name = "investigate_question"
    README_CANDIDATES = (
        "README.md",
        "README.rst",
        "README.txt",
        "README",
        "readme.md",
    )
    BUILD_FILE_CANDIDATES = (
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
        "package.json",
        "pnpm-workspace.yaml",
        "pnpm-lock.yaml",
        "yarn.lock",
        "package-lock.json",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "go.sum",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "Makefile",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "composer.json",
        "Gemfile",
        "mix.exs",
    )
    SOURCE_DIR_HINTS = ("src", "app", "cmd", "server", "backend", "frontend", "packages")
    SOURCE_FILE_HINTS = (
        "main.py",
        "__main__.py",
        "app.py",
        "cli.py",
        "server.py",
        "index.ts",
        "index.tsx",
        "index.js",
        "index.jsx",
        "main.ts",
        "main.tsx",
        "main.js",
        "main.jsx",
        "main.go",
    )
    SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"}

    def _run_with_llm(self, skill_input: SkillInput, context: AgentContext):
        self._bootstrap_repo_evidence(skill_input, context)
        return super()._run_with_llm(skill_input, context)

    def build_state_updates(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> dict[str, Any]:
        findings = result.get("findings", [])
        evidence_gaps = result.get("evidence_gaps", [])
        return {
            "latest_investigation": result,
            "findings": findings if isinstance(findings, list) else [],
            "open_questions": evidence_gaps if isinstance(evidence_gaps, list) else [],
            "investigation_summary": result.get("investigation_summary"),
        }

    def build_next_actions(self, result: dict[str, Any], skill_input: SkillInput, context: AgentContext) -> list[str]:
        evidence_gaps = result.get("evidence_gaps", [])
        return [str(item) for item in evidence_gaps] if isinstance(evidence_gaps, list) else []

    def build_fallback_result(
        self,
        skill_input: SkillInput,
        context: AgentContext,
        messages: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        open_questions = skill_input.workflow_state.get("open_questions", [])
        findings = skill_input.workflow_state.get("findings", [])
        fallback_claim = f"Collected evidence for objective `{skill_input.objective or 'general_repository_question'}`."
        if skill_input.question:
            fallback_claim = f"Collected repository evidence to answer: {skill_input.question}"
        return {
            "investigation_summary": "The model completed tool-based evidence collection but failed to emit fully valid JSON; using a minimal recovered investigation result.",
            "evidence": sorted(context.read_files)[:8],
            "findings": findings[:6] if isinstance(findings, list) else [
                {
                    "claim": fallback_claim,
                    "importance": "medium",
                    "evidence": sorted(context.read_files)[:4],
                    "related_files": sorted(context.read_files)[:4],
                }
            ],
            "evidence_gaps": [str(item) for item in open_questions[:6]] if isinstance(open_questions, list) else [],
            "uncertainties": ["LLM output formatting was unstable; investigation result was minimally recovered."],
        }

    def output_schema_text(self) -> str:
        return """
{
  "investigation_summary": "string",
  "evidence": ["string"],
  "findings": [
    {
      "claim": "string",
      "importance": "high|medium|low",
      "evidence": ["string"],
      "related_files": ["string"]
    }
  ],
  "evidence_gaps": ["string"],
  "uncertainties": ["string"]
}
""".strip()

    def _bootstrap_repo_evidence(self, skill_input: SkillInput, context: AgentContext) -> None:
        repo_root = Path(skill_input.repo_path).resolve()
        toolkit = RepoToolkit(skill_input.repo_path, context)

        if not any(log.tool_name == "get_file_tree" for log in context.tool_logs):
            toolkit.execute("get_file_tree", {"path": ".", "max_depth": 3})

        if context.read_files:
            return

        candidates = self._select_bootstrap_files(repo_root)
        if candidates:
            toolkit.execute("read_files", {"paths": candidates, "start_line": 1, "end_line": 220})

    def _select_bootstrap_files(self, repo_root: Path) -> list[str]:
        ordered: list[Path] = []
        ordered.extend(self._existing_paths(repo_root, self.README_CANDIDATES))
        ordered.extend(self._existing_paths(repo_root, self.BUILD_FILE_CANDIDATES))

        if not ordered:
            ordered.extend(self._discover_fallback_files(repo_root))
        else:
            ordered.extend(self._discover_fallback_files(repo_root, limit=3))

        unique: list[str] = []
        seen: set[Path] = set()
        for path in ordered:
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            unique.append(str(path.relative_to(repo_root)))
            if len(unique) >= 6:
                break
        return unique

    def _existing_paths(self, repo_root: Path, names: tuple[str, ...]) -> list[Path]:
        paths: list[Path] = []
        for name in names:
            path = repo_root / name
            if path.is_file():
                paths.append(path)
        return paths

    def _discover_fallback_files(self, repo_root: Path, limit: int = 6) -> list[Path]:
        direct_candidates: list[Path] = []
        for relative in self.SOURCE_FILE_HINTS:
            candidate = repo_root / relative
            if candidate.is_file():
                direct_candidates.append(candidate)
        for dirname in self.SOURCE_DIR_HINTS:
            directory = repo_root / dirname
            if not directory.is_dir():
                continue
            for filename in self.SOURCE_FILE_HINTS:
                candidate = directory / filename
                if candidate.is_file():
                    direct_candidates.append(candidate)

        discovered: list[Path] = []
        for path in direct_candidates + list(self._walk_repo_files(repo_root, max_depth=3)):
            if path in discovered:
                continue
            discovered.append(path)
            if len(discovered) >= limit:
                break
        return discovered

    def _walk_repo_files(self, repo_root: Path, max_depth: int) -> list[Path]:
        collected: list[Path] = []

        def visit(directory: Path, depth: int) -> None:
            if depth > max_depth:
                return
            for child in sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
                if should_ignore(child, repo_root):
                    continue
                if child.is_file():
                    if child.suffix in self.SOURCE_SUFFIXES:
                        collected.append(child)
                elif depth < max_depth:
                    visit(child, depth + 1)

        visit(repo_root, 1)
        return collected
