# Question-Driven Stateful Reasoning Workflow Blueprint

## Goal

Replace the current skill-first pipeline with a question-driven workflow that can answer different repository-understanding questions without forcing them into a small fixed skill taxonomy.

The CLI contract remains unchanged:

```bash
repo-guide-agent --repo /path/to/repo --question "..."
```

## Core Shift

Old core logic:

1. parse a single intent
2. map intent to a fixed skill list
3. run the list in order
4. format outputs

New core logic:

1. model the user's question into a compact question model
2. investigate the repository with evidence goals derived from that model
3. synthesize a direct answer draft from accumulated state
4. verify whether the draft actually answers the question
5. if verification fails, run another focused investigation pass

## Main Components

### 1. Question Modeler

Produces a structured `ParsedQuery` that includes:

- `objective`: what kind of repository-understanding task this is
- `answer_mode`: what shape the answer should have
- `key_entities`: entities or targets named in the question
- `required_evidence`: categories of evidence the workflow should collect
- `investigation_focus`: the first things to inspect
- `expected_sections`: the likely answer structure

`intent` is retained only as a backward-compatible hint.

### 2. Workflow Graph

The workflow graph is generic rather than task-specific.

Default graph:

1. `investigate_question` pass 1
2. `synthesize_answer` pass 1
3. `verify_answer` pass 1
4. conditional retry to `investigate_question` pass 2 if answer is not ready
5. `synthesize_answer` pass 2
6. `verify_answer` pass 2

This graph is state-driven, not intent-driven.

### 3. Shared Workflow State

State fields should include:

- `question_model`
- `findings`
- `evidence_pool`
- `open_questions`
- `draft_answer`
- `coverage_points`
- `verification_result`
- `answer_ready`
- `investigation_round`
- `max_investigation_rounds`

### 4. Generic Reasoning Nodes

#### `investigate_question`

- tool-using node
- collects targeted evidence
- updates findings, evidence pool, and evidence gaps

#### `synthesize_answer`

- non-tool node
- transforms current state into a direct answer draft
- aligns the structure with the question model

#### `verify_answer`

- non-tool node
- checks coverage and evidence support
- either marks the answer ready or requests another investigation pass

## Execution Rules

1. `investigate_question` should read only the files needed to support the answer.
2. `synthesize_answer` should produce a user-facing answer draft, not another repository summary.
3. `verify_answer` should reject answers that are merely related but not question-shaped.
4. Conditional edges should depend on workflow state, especially `answer_ready` and retry count.
5. The workflow should stop once the answer is ready or retry budget is exhausted.

## Why This Is More General

This design is general across repository-understanding questions because it does not assume that a question belongs to a prebuilt skill bucket. Instead, it adapts the evidence plan and answer shape to the question itself.

Examples it should handle better:

- repository overview
- entrypoint discovery
- module explanation
- symbol trace
- execution flow explanation
- reading plan generation
- mixed questions that require multiple evidence types
