from __future__ import annotations

from src.skills.base import BaseSkill


class ExplainModuleSkill(BaseSkill):
    name = "explain_module"

    def output_schema_text(self) -> str:
        return """
{
  "module_path": "string",
  "module_role": "string",
  "evidence": ["string"],
  "key_files": [{"path": "string", "role": "string"}],
  "key_symbols": [{"name": "string", "type": "class|function|variable", "role": "string"}],
  "upstream_dependencies": ["string"],
  "downstream_consumers": ["string"],
  "uncertainties": ["string"]
}
""".strip()
