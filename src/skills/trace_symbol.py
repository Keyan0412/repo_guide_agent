from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill
from src.tools.symbol_search import search_symbol


class TraceSymbolSkill(BaseSkill):
    name = "trace_symbol"

    def fallback_run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        if not skill_input.symbol_name:
            raise ValueError("symbol_name is required for trace_symbol")
        context.log_tool("search_symbol", {"root_path": skill_input.repo_path, "symbol_name": skill_input.symbol_name, "top_k": 20})
        results = search_symbol(skill_input.repo_path, skill_input.symbol_name, top_k=20)
        definitions = [
            {"path": hit.path, "line": hit.line, "signature": hit.snippet}
            for hit in results["definitions"]
            if "test" not in hit.path.lower()
        ]
        references = [
            {"path": hit.path, "line": hit.line, "usage_role": hit.snippet}
            for hit in results["references"]
            if "test" not in hit.path.lower()
        ]
        chain = []
        if definitions:
            chain.append({"path": definitions[0]["path"], "symbol": skill_input.symbol_name, "role": "definition"})
        for ref in references[:2]:
            chain.append({"path": ref["path"], "symbol": skill_input.symbol_name, "role": "reference"})
        uncertainties = [] if definitions else ["未定位到明确的定义，可能存在动态注册、重名或语言规则未覆盖。"]
        data = {
            "symbol_name": skill_input.symbol_name,
            "definitions": definitions[:5],
            "references": references[:8],
            "most_likely_call_chain": chain,
            "conclusion": "Returned the best-effort definition and surrounding references using regex-based symbol search.",
            "uncertainties": uncertainties,
        }
        output = SkillOutput(skill_name=self.name, data=data, evidence=[str(item) for item in chain], uncertainties=uncertainties)
        return output

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
