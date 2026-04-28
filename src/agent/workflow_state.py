from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from src.schemas.response_models import ExecutionPlan, ParsedQuery


@dataclass
class WorkflowState:

    # from parsed query
    question: str | None = None
    question_model: dict[str, Any] = field(default_factory=dict)
    objective: str = "answer_repo_question"
    answer_mode: str = "direct_answer"
    required_evidence: list[str] = field(default_factory=list)

    # workflow information
    completed_nodes: list[str] = field(default_factory=list)
    completed_skills: list[str] = field(default_factory=list)
    last_skill: str | None = None
    last_node: str | None = None
    investigation_round: int = 0
    max_investigation_rounds: int = 2
    answer_ready: bool = False

    # product of previous skills
    outputs_by_skill: dict[str, dict[str, Any]] = field(default_factory=dict)
    evidence_pool: list[str] = field(default_factory=list)
    findings: list[Any] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    # information for reply
    draft_answer: str | None = None
    coverage_points: list[str] = field(default_factory=list)
    verification_result: dict[str, Any] | None = None
    verifier_feedback: dict[str, Any] = field(default_factory=dict)
    latest_investigation: dict[str, Any] | None = None
    investigation_summary: str | None = None
    latest_synthesized_answer: dict[str, Any] | None = None

    @classmethod
    def from_query(cls, parsed_query: ParsedQuery, plan: ExecutionPlan) -> WorkflowState:
        return cls(
            question=parsed_query.question,
            question_model=parsed_query.model_dump(),
            objective=parsed_query.objective,
            answer_mode=parsed_query.answer_mode,
            required_evidence=list(parsed_query.required_evidence),
            open_questions=list(parsed_query.investigation_focus),
        )

    def update(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if not hasattr(self, key):
                raise KeyError(f"Unknown workflow state field: {key}")
            setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
