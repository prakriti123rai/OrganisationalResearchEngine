from __future__ import annotations

import json
from typing import Any

from app.schemas.reasoning import ReasoningResult


class ReasoningParseError(ValueError):
    pass


def extract_response_json(response_payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(response_payload.get("output_text"), str):
        return _loads(response_payload["output_text"])

    for output in response_payload.get("output", []):
        for content in output.get("content", []):
            if content.get("type") in {"output_text", "text"} and isinstance(
                content.get("text"), str
            ):
                return _loads(content["text"])
    raise ReasoningParseError("GPT reasoning response did not include JSON text.")


def parse_reasoning_result(
    result_payload: dict[str, Any],
    *,
    model: str,
    provider: str,
) -> ReasoningResult:
    result_payload["model"] = model
    result_payload["provider"] = provider
    try:
        return ReasoningResult.model_validate(result_payload)
    except ValueError as exc:
        raise ReasoningParseError(f"GPT reasoning response did not match schema: {exc}") from exc


def _loads(raw_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ReasoningParseError(f"GPT reasoning response was malformed JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReasoningParseError("GPT reasoning response JSON must be an object.")
    return payload
