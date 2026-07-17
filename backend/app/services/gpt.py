from __future__ import annotations

from app.reasoning.gpt_adapter import GPTAdapter
from app.schemas.reasoning import ReasoningResult


class GPTReasoningService:
    def __init__(
        self,
        *,
        api_key: str,
        responses_url: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.adapter = GPTAdapter(
            api_key=api_key,
            responses_url=responses_url,
            model=model,
            timeout_seconds=timeout_seconds,
        )

    def reason(self, *, prompt_payload: dict, schema: dict) -> ReasoningResult:
        return self.adapter.reason(prompt_payload=prompt_payload, schema=schema)
