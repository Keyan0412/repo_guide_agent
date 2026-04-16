from __future__ import annotations

from src.skills.base import BaseSkill


class TraceSymbolSkill(BaseSkill):
    name = "trace_symbol"

    def output_schema_text(self) -> str:
        return """
{
  "symbol_name": "string",
  "definitions": [{"path": "string", "line": 0, "signature": "string"}],
  "references": [{"path": "string", "line": 0, "usage_role": "string"}],
  "most_likely_call_chain": [{"path": "string", "symbol": "string", "role": "string"}],
  "conclusion": "string",
  "uncertainties": ["string"]
}
""".strip()
