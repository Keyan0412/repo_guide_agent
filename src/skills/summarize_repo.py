from __future__ import annotations

from pathlib import Path

from src.agent.context import AgentContext
from src.parsers.dependency_parser import detect_frameworks
from src.parsers.language_detector import detect_primary_language
from src.parsers.readme_parser import extract_project_purpose, extract_run_commands
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.tools.file_tree import get_file_tree
from src.utils.repo_stats import collect_extension_stats
from src.utils.text import repo_name, shorten


class SummarizeRepoSkill(BaseSkill):
    name = "summarize_repo"

    def fallback_run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        root = Path(skill_input.repo_path).resolve()
        context.log_tool("get_file_tree", {"root_path": str(root), "max_depth": 3})
        tree = get_file_tree(str(root), max_depth=3)
        extension_stats = collect_extension_stats(root)
        primary_language = detect_primary_language(extension_stats, root)
        frameworks = detect_frameworks(root)

        readme_path = next((p for p in [root / "README.md", root / "readme.md"] if p.exists()), None)
        purpose = ""
        run_commands: list[str] = []
        evidence = [f"顶层目录: {', '.join(tree.top_level_entries[:8])}"]
        uncertainties: list[str] = []
        if readme_path:
            context.read_files.add(str(readme_path))
            readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")
            purpose = extract_project_purpose(readme_text)
            run_commands = extract_run_commands(readme_text)
            evidence.append(f"README: {readme_path.name}")
        else:
            uncertainties.append("未找到 README，项目用途主要依赖目录与依赖文件推断。")

        project_type = "unknown"
        lowered = " ".join(frameworks).lower() + " " + " ".join(run_commands).lower()
        if any(token in lowered for token in ["fastapi", "flask", "django", "uvicorn", "express", "next.js"]):
            project_type = "web"
        elif any(token in lowered for token in ["typer", "click", "argparse", "cli"]):
            project_type = "cli"
        elif any(token in lowered for token in ["torch", "trainer", "train", "fit", "transformers"]):
            project_type = "training"

        top_level_modules = []
        for entry in tree.top_level_entries[:8]:
            role = "source_or_module" if entry.endswith("/") else "config_or_doc"
            top_level_modules.append({"path": entry, "role": role})

        likely_purpose = purpose or f"{repo_name(root)} appears to be a {project_type} repository written mainly in {primary_language}."
        data = {
            "repo_name": repo_name(root),
            "likely_purpose": shorten(likely_purpose, 320),
            "primary_language": primary_language,
            "frameworks": frameworks,
            "project_type": project_type,
            "top_level_modules": top_level_modules,
            "run_commands": run_commands,
            "key_evidence": evidence,
            "uncertainties": uncertainties,
        }
        output = SkillOutput(skill_name=self.name, data=data, evidence=evidence, uncertainties=uncertainties)
        return output

    def output_schema_text(self) -> str:
        return """
{
  "repo_name": "string",
  "likely_purpose": "string",
  "primary_language": "string",
  "frameworks": ["string"],
  "project_type": "web|cli|training|library|unknown",
  "top_level_modules": [{"path": "string", "role": "string"}],
  "run_commands": ["string"],
  "key_evidence": ["string"],
  "uncertainties": ["string"]
}
""".strip()
