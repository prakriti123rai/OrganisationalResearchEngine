from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.reasoning.reasoning_parser import extract_response_json, parse_reasoning_result
from app.schemas.reasoning import ReasoningResult


class GPTAdapterError(RuntimeError):
    pass


class GPTAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        responses_url: str,
        model: str,
        timeout_seconds: int,
    ) -> None:
        self.api_key = api_key
        self.responses_url = responses_url
        self.model = model
        self.timeout_seconds = timeout_seconds

    def reason(self, *, prompt_payload: dict[str, Any], schema: dict[str, Any]) -> ReasoningResult:
        body = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You are the ORE GPT-5.5 reasoning engine. Return only JSON "
                        "that conforms to the requested schema. Ground every claim in "
                        "the provided canonical context ids."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, sort_keys=True),
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "ore_reasoning_result",
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            self.responses_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GPTAdapterError(f"OpenAI reasoning request failed: {detail}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise GPTAdapterError(f"OpenAI reasoning request failed: {exc}") from exc

        try:
            return parse_reasoning_result(
                extract_response_json(response_payload),
                model=self.model,
                provider="openai_responses",
            )
        except ValueError as exc:
            raise GPTAdapterError(str(exc)) from exc
