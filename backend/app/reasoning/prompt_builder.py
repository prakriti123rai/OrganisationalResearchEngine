from __future__ import annotations

from pathlib import Path
from typing import Any

from app.schemas.reasoning_context import ReasoningContextRead

REASONING_PROMPT_VERSION = "reasoning_prompt_v1"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "reasoning_prompt.md"


def build_prompt_payload(context: ReasoningContextRead) -> dict[str, Any]:
    return {
        "prompt_version": REASONING_PROMPT_VERSION,
        "instructions": PROMPT_PATH.read_text(encoding="utf-8"),
        "task": "Assess organizational impact for this pull request.",
        "question": context.question,
        "pattern": context.pattern,
        "pull_request": context.pull_request.model_dump(mode="json"),
        "scope": context.scope.model_dump(mode="json"),
        "sections": [section.model_dump(mode="json") for section in context.sections],
        "nodes": [node.model_dump(mode="json") for node in context.nodes],
        "edges": [edge.model_dump(mode="json") for edge in context.edges],
        "evidence": [evidence.model_dump(mode="json") for evidence in context.evidence],
        "signals": [signal.model_dump(mode="json") for signal in context.signals],
        "assumptions": [assumption.model_dump(mode="json") for assumption in context.assumptions],
    }
