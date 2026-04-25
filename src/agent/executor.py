from __future__ import annotations

from typing import Callable

from src.agent.context import AgentContext
from src.llm.client import LLMClient
from src.schemas.response_models import ExecutionPlan, ParsedQuery, WorkflowNode
from src.schemas.skill_io import SkillInput, SkillOutput
from src.skills.investigate_question import InvestigateQuestionSkill
from src.skills.synthesize_answer import SynthesizeAnswerSkill
from src.skills.verify_answer import VerifyAnswerSkill


class Executor:
    def __init__(self, llm_client: LLMClient | None = None, reporter: Callable[[str], None] | None = None) -> None:
        llm_client = llm_client or LLMClient()
        self.reporter = reporter
        self.skills = {
            "investigate_question": InvestigateQuestionSkill(llm_client=llm_client),
            "synthesize_answer": SynthesizeAnswerSkill(llm_client=llm_client),
            "verify_answer": VerifyAnswerSkill(llm_client=llm_client),
        }

    def execute_plan(
        self,
        parsed_query: ParsedQuery,
        plan: ExecutionPlan,
        verbose: bool = False,
        show_progress: bool = False,
    ) -> tuple[AgentContext, list[SkillOutput]]:
        context = AgentContext(
            repo_path=parsed_query.repo_path,
            verbose=verbose,
            progress_enabled=show_progress,
            reporter=self.reporter,
        )
        context.workflow_state = self._build_initial_state(parsed_query, plan)
        context.emit(f"[executor:start] repo={parsed_query.repo_path}")
        outputs: list[SkillOutput] = []
        current_node_id: str | None = plan.entry_node_id
        visited_counts: dict[str, int] = {}
        while current_node_id:
            visited_counts[current_node_id] = visited_counts.get(current_node_id, 0) + 1
            if visited_counts[current_node_id] > 2:
                raise RuntimeError(f"Workflow loop exceeded retry budget at node {current_node_id}")
            node = plan.get_node(current_node_id)
            context.log_workflow_node(node.node_id, node.node_type, node.name, "start")
            output = self._execute_node(node, parsed_query, context)
            context.log_workflow_node(node.node_id, node.node_type, node.name, "done")
            if output is not None:
                outputs.append(output)
            current_node_id = self._next_node_id(plan, node.node_id, context)
        context.emit("[executor:done] all skills completed")
        return context, outputs

    def _build_initial_state(self, parsed_query: ParsedQuery, plan: ExecutionPlan) -> dict:
        return {
            "repo_path": parsed_query.repo_path,
            "question": parsed_query.question,
            "question_model": parsed_query.model_dump(),
            "objective": parsed_query.objective,
            "answer_mode": parsed_query.answer_mode,
            "required_evidence": list(parsed_query.required_evidence),
            "completed_nodes": [],
            "completed_skills": [],
            "outputs_by_skill": {},
            "findings": [],
            "evidence_pool": [],
            "open_questions": list(parsed_query.investigation_focus),
            "draft_answer": None,
            "coverage_points": [],
            "verification_result": None,
            "verifier_feedback": {},
            "answer_ready": False,
            "investigation_round": 0,
            "max_investigation_rounds": 2,
            "last_skill": None,
            "last_node": None,
        }

    def _execute_node(self, node: WorkflowNode, parsed_query: ParsedQuery, context: AgentContext) -> SkillOutput:
        context.emit(f"[executor] running step={node.name} args={node.args}")
        merged_input = self._build_skill_input(parsed_query, node.args, context.workflow_state)
        output = self.skills[node.name].run(merged_input, context)
        self._apply_skill_output(node, output, context)
        return output

    def _apply_skill_output(self, node: WorkflowNode, output: SkillOutput, context: AgentContext) -> None:
        completed_nodes = list(context.workflow_state.get("completed_nodes", []))
        completed_nodes.append(node.node_id)
        completed_skills = list(context.workflow_state.get("completed_skills", []))
        completed_skills.append(output.skill_name)
        outputs_by_skill = dict(context.workflow_state.get("outputs_by_skill", {}))
        outputs_by_skill[node.node_id] = output.data

        evidence_pool = list(context.workflow_state.get("evidence_pool", []))
        evidence_pool.extend(item for item in output.evidence if item not in evidence_pool)

        findings = list(context.workflow_state.get("findings", []))
        new_findings = output.state_updates.get("findings", [])
        if isinstance(new_findings, list):
            findings.extend(item for item in new_findings if item not in findings)

        open_questions = list(context.workflow_state.get("open_questions", []))
        derived_open_questions = output.state_updates.get("open_questions", [])
        if isinstance(derived_open_questions, list):
            open_questions = [str(item) for item in derived_open_questions]
        if output.uncertainties:
            for item in output.uncertainties:
                if item not in open_questions:
                    open_questions.append(item)

        workflow_updates = {
            "last_skill": output.skill_name,
            "last_node": node.node_id,
            "completed_nodes": completed_nodes,
            "completed_skills": completed_skills,
            "outputs_by_skill": outputs_by_skill,
            "evidence_pool": evidence_pool,
            "findings": findings,
        }
        if output.skill_name == "investigate_question":
            workflow_updates["investigation_round"] = int(context.workflow_state.get("investigation_round", 0)) + 1
        context.update_workflow_state(workflow_updates)
        context.update_workflow_state(output.state_updates)
        context.update_workflow_state({"open_questions": open_questions, "next_actions": output.next_actions})
        context.uncertainties = list(dict.fromkeys(open_questions))

    def _next_node_id(self, plan: ExecutionPlan, current_node_id: str, context: AgentContext) -> str | None:
        for edge in plan.edges:
            if edge.source == current_node_id and self._edge_is_open(edge.condition, context):
                return edge.target
        return None

    def _edge_is_open(self, condition: str, context: AgentContext) -> bool:
        if condition == "always":
            return True
        if condition == "needs_followup":
            return (
                not bool(context.workflow_state.get("answer_ready"))
                and int(context.workflow_state.get("investigation_round", 0)) < int(context.workflow_state.get("max_investigation_rounds", 2))
            )
        return False

    def _build_skill_input(self, parsed_query: ParsedQuery, call_args: dict, workflow_state: dict) -> SkillInput:
        base = SkillInput(
            repo_path=parsed_query.repo_path,
            question=parsed_query.question,
            objective=parsed_query.objective,
            answer_mode=parsed_query.answer_mode,
            required_evidence=list(parsed_query.required_evidence),
            investigation_focus=list(parsed_query.investigation_focus),
            workflow_state=dict(workflow_state),
        )
        return base.model_copy(update=call_args)
