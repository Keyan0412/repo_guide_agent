from __future__ import annotations

from src.agent.context import AgentContext
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.base import BaseSkill


class GenerateReadingPlanSkill(BaseSkill):
    name = "generate_reading_plan"

    def fallback_run(self, skill_input: SkillInput, context: AgentContext) -> SkillOutput:
        summary = context.previous_results.get("summarize_repo")
        entries = context.previous_results.get("find_entrypoints")
        goal = skill_input.user_goal or "理解核心链路"
        steps = []
        order = 1
        for candidate in (entries.data.get("entry_candidates", []) if entries else []):
            steps.append(
                {
                    "order": order,
                    "path": candidate["path"],
                    "why_read": "从最可能的入口开始建立主链路。",
                    "focus_points": ["初始化过程", "参数解析", "依赖装配"],
                }
            )
            order += 1
        for module in (summary.data.get("top_level_modules", []) if summary else [])[:3]:
            steps.append(
                {
                    "order": order,
                    "path": module["path"],
                    "why_read": "补足顶层结构与模块边界。",
                    "focus_points": ["目录职责", "核心实现", "与入口关系"],
                }
            )
            order += 1
        if not steps:
            steps.append(
                {
                    "order": 1,
                    "path": ".",
                    "why_read": "缺少前置结果时，先从 README 和顶层目录开始。",
                    "focus_points": ["README", "依赖文件", "主源码目录"],
                }
            )
        data = {
            "user_goal": goal,
            "reading_steps": steps,
            "suggested_stop_condition": "能够说清入口、核心模块分工以及目标功能从哪里开始执行。",
            "uncertainties": [],
        }
        output = SkillOutput(skill_name=self.name, data=data, evidence=[step["path"] for step in steps], uncertainties=[])
        return output

    def output_schema_text(self) -> str:
        return """
{
  "user_goal": "string",
  "reading_steps": [
    {
      "order": 1,
      "path": "string",
      "why_read": "string",
      "focus_points": ["string"]
    }
  ],
  "suggested_stop_condition": "string",
  "uncertainties": ["string"]
}
""".strip()
