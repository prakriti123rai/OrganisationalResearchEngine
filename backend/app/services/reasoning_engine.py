from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.reasoning_session import ReasoningSession
from app.reasoning.prompt_builder import REASONING_PROMPT_VERSION, build_prompt_payload
from app.reasoning.reasoning_report import build_deterministic_reasoning_report
from app.schemas.reasoning import ReasoningResult, ReasoningRunRead
from app.schemas.reasoning_context import ReasoningContextRead
from app.schemas.reasoning_session import ReasoningSessionRead
from app.services.exceptions import NotFoundError, ValidationError
from app.services.gpt import GPTReasoningService
from app.services.reasoning_context import ReasoningContextService


class ReasoningExecutionError(RuntimeError):
    """Raised when a configured model provider cannot return a valid reasoning result."""


class ReasoningEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    def run_session(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
        graph_depth: int = 2,
        force: bool = False,
    ) -> ReasoningRunRead:
        session = self._get_reasoning_session(organization_id, reasoning_session_id)
        if session.report is not None and session.status == "completed" and not force:
            return self._to_run_read(organization_id, session, session.report)

        context = ReasoningContextService(self.db).build_for_session(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            graph_depth=graph_depth,
        )

        session.status = "running"
        self.db.flush()

        started_at = perf_counter()
        try:
            result = self.reason_context(context=context, started_at=started_at)
        except Exception as exc:
            session.status = "failed"
            session.context_metadata = {
                **session.context_metadata,
                "reasoning_engine": {
                    "model": self.settings.reasoning_model,
                    "provider": self._provider_name(),
                    "error": str(exc),
                    "prompt_version": REASONING_PROMPT_VERSION,
                    "completed_at": self._now_iso(),
                },
            }
            self.db.commit()
            raise ReasoningExecutionError(str(exc)) from exc

        result_payload = result.model_dump(mode="json")
        session.status = "completed"
        session.report = result_payload
        session.completed_at = datetime.now(timezone.utc)
        session.context_metadata = {
            **session.context_metadata,
            "reasoning_engine": {
                "schema_version": result.schema_version,
                "model": result.model,
                "provider": result.provider,
                "graph_depth": graph_depth,
                "prompt_version": result.metadata.get("prompt_version"),
                "execution_time_ms": result.metadata.get("execution_time_ms"),
                "completed_at": self._now_iso(),
            },
        }
        self.db.commit()
        self.db.refresh(session)
        return self._to_run_read(organization_id, session, result_payload)

    def get_result(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
    ) -> ReasoningRunRead:
        session = self._get_reasoning_session(organization_id, reasoning_session_id)
        if session.report is None:
            raise ValidationError(f"Reasoning session '{reasoning_session_id}' has no result yet.")
        return self._to_run_read(organization_id, session, session.report)

    def reason_context(
        self,
        *,
        context: ReasoningContextRead,
        started_at: float | None = None,
    ) -> ReasoningResult:
        started = started_at if started_at is not None else perf_counter()
        if self.settings.openai_api_key:
            result = GPTReasoningService(
                api_key=self.settings.openai_api_key,
                responses_url=self.settings.openai_responses_url,
                model=self.settings.reasoning_model,
                timeout_seconds=self.settings.openai_timeout_seconds,
            ).reason(
                prompt_payload=build_prompt_payload(context),
                schema=self._json_schema(),
            )
            result.metadata = {
                **result.metadata,
                "prompt_version": REASONING_PROMPT_VERSION,
                "execution_time_ms": max(0, int((perf_counter() - started) * 1000)),
            }
            return result

        return build_deterministic_reasoning_report(
            context=context,
            model=self.settings.reasoning_model,
            prompt_version=REASONING_PROMPT_VERSION,
            execution_time_ms=max(0, int((perf_counter() - started) * 1000)),
        )

    def _json_schema(self) -> dict[str, Any]:
        return ReasoningResult.model_json_schema()

    def _to_run_read(
        self,
        organization_id: str,
        session: ReasoningSession,
        result_payload: dict[str, Any],
    ) -> ReasoningRunRead:
        return ReasoningRunRead(
            organization_id=organization_id,
            reasoning_session=ReasoningSessionRead.model_validate(session),
            result=ReasoningResult.model_validate(result_payload),
            context_metadata=session.context_metadata,
        )

    def _get_reasoning_session(
        self, organization_id: str, reasoning_session_id: str
    ) -> ReasoningSession:
        session = self.db.get(ReasoningSession, reasoning_session_id)
        if session is None or session.organization_id != organization_id:
            raise NotFoundError(
                f"Reasoning session '{reasoning_session_id}' was not found in "
                f"organization '{organization_id}'."
            )
        if session.pull_request_id is None:
            raise ValidationError(
                f"Reasoning session '{reasoning_session_id}' is not linked to a pull request."
            )
        return session

    def _provider_name(self) -> str:
        return "openai_responses" if self.settings.openai_api_key else "deterministic_local"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
