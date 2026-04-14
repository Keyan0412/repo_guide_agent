from __future__ import annotations

from pathlib import Path

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.tools.file_tree import get_file_tree
from src.tools.symbol_search import search_symbol


class ExplainModuleSkill(BaseSkill):
    name = "explain_module"

    def fallback_run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        if not skill_input.module_path:
            raise ValueError("module_path is required for explain_module")
        root = Path(skill_input.repo_path).resolve()
        module = (root / skill_input.module_path).resolve()
        context.log_tool("get_file_tree", {"root_path": str(module), "max_depth": 2})
        tree = get_file_tree(str(module), max_depth=2)
        key_symbols = []
        for candidate in ["main", "run", "train", "App", "Config"]:
            symbol_hits = search_symbol(str(module), candidate, top_k=3)
            for hit in symbol_hits["definitions"]:
                key_symbols.append({"name": candidate, "type": "definition", "role": hit.snippet})
        data = {
            "module_path": str(module.relative_to(root)),
            "module_role": f"Module with {len(tree.top_level_entries)} immediate entries.",
            "key_files": [{"path": f, "role": "candidate"} for f in tree.top_level_entries[:8]],
            "key_symbols": key_symbols[:10],
            "upstream_dependencies": [],
            "downstream_consumers": [],
            "uncertainties": [],
        }
        output = SkillOutput(skill_name=self.name, data=data, evidence=[tree.tree_text], uncertainties=[])
        return output

    def output_schema_text(self) -> str:
        return """
{
  "module_path": "string",
  "module_role": "string",
  "key_files": [{"path": "string", "role": "string"}],
  "key_symbols": [{"name": "string", "type": "class|function|variable", "role": "string"}],
  "upstream_dependencies": ["string"],
  "downstream_consumers": ["string"],
  "uncertainties": ["string"]
}
""".strip()
