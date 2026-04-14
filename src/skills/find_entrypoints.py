from __future__ import annotations

import re
from pathlib import Path

from src.agent.context import AgentContext
from src.parsers.readme_parser import extract_run_commands
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.tools.keyword_search import search_keyword


class FindEntrypointsSkill(BaseSkill):
    name = "find_entrypoints"

    def fallback_run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        root = Path(skill_input.repo_path).resolve()
        readme_commands: list[str] = []
        for readme in (root / "README.md", root / "readme.md"):
            if readme.exists():
                readme_commands = extract_run_commands(readme.read_text(encoding="utf-8", errors="ignore"))
                break
        patterns = [
            "__main__",
            "argparse",
            "typer",
            "click",
            "uvicorn.run",
            "FastAPI",
            "Flask(",
            "train(",
            "main(",
        ]
        hits = []
        for pattern in patterns:
            context.log_tool("search_keyword", {"root_path": str(root), "query": pattern, "top_k": 10})
            hits.extend(search_keyword(str(root), pattern, top_k=10))

        candidates: dict[str, dict] = {}
        for hit in hits:
            path = hit.path
            lowered_path = path.lower()
            if lowered_path.endswith((".md", ".rst", ".txt")):
                continue
            score = candidates.setdefault(path, {"score": 0, "evidence": [], "entry_type": "unknown"})
            score["evidence"].append(f"{path}:{hit.line} {hit.snippet}")
            snippet_lower = hit.snippet.lower()
            if "__main__" in hit.snippet or re.search(r"\bmain\s*\(", hit.snippet):
                score["score"] += 2
            if any(token in snippet_lower for token in ["fastapi", "uvicorn", "flask"]):
                score["score"] += 2
                score["entry_type"] = "web"
            if any(token in snippet_lower for token in ["argparse", "typer", "click"]):
                score["score"] += 2
                score["entry_type"] = "cli"
            if "train" in snippet_lower or "trainer" in snippet_lower or "fit(" in snippet_lower:
                score["score"] += 2
                if score["entry_type"] == "unknown":
                    score["entry_type"] = "training"
            if any(token in lowered_path for token in ["test", "example", "demo"]):
                score["score"] -= 2
            if any(token in lowered_path for token in ["docs/", "prompts/", "spec", "skill"]):
                score["score"] -= 3
            if any(token in lowered_path for token in ["main", "app", "server", "train", "cli"]):
                score["score"] += 1
            if any(fragment in " ".join(readme_commands) for fragment in [path, Path(path).name]):
                score["score"] += 3
                score["evidence"].append(f"README command mentions {Path(path).name}")

        ranked = sorted(candidates.items(), key=lambda item: item[1]["score"], reverse=True)[:3]
        entry_candidates = []
        for path, payload in ranked:
            confidence = max(0.1, min(0.99, 0.5 + payload["score"] * 0.08))
            entry_candidates.append(
                {
                    "path": path,
                    "entry_type": payload["entry_type"],
                    "confidence": round(confidence, 2),
                    "reason": "Matched common bootstrap patterns and file naming heuristics.",
                    "supporting_evidence": payload["evidence"][:4],
                }
            )
        uncertainties = [] if entry_candidates else ["未找到明显入口模式，可能需要结合 README 或脚本进一步确认。"]
        data = {
            "entry_candidates": entry_candidates,
            "recommended_first_read": [candidate["path"] for candidate in entry_candidates],
            "uncertainties": uncertainties,
        }
        output = SkillOutput(skill_name=self.name, data=data, evidence=[c["path"] for c in entry_candidates], uncertainties=uncertainties)
        return output

    def output_schema_text(self) -> str:
        return """
{
  "entry_candidates": [
    {
      "path": "string",
      "entry_type": "web|cli|training|service|unknown",
      "confidence": 0.0,
      "reason": "string",
      "supporting_evidence": ["string"]
    }
  ],
  "recommended_first_read": ["string"],
  "uncertainties": ["string"]
}
""".strip()
