from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.reasoning_session import ReasoningSession
from app.reasoning.prompt_builder import REASONING_PROMPT_VERSION, build_prompt_payload
from app.reasoning.reasoning_report import build_deterministic_reasoning_report
from app.schemas.reasoning import (
    ReasoningResult,
    ReasoningRunRead,
    ReasoningTraceArtifact,
    ReasoningTraceRead,
    ReasoningTraceStage,
)
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

    def get_trace(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
        graph_depth: int = 2,
    ) -> ReasoningTraceRead:
        session = self._get_reasoning_session(organization_id, reasoning_session_id)
        if session.report is None:
            raise ValidationError(f"Reasoning session '{reasoning_session_id}' has no result yet.")

        context = ReasoningContextService(self.db).build_for_session(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            graph_depth=graph_depth,
        )
        result = ReasoningResult.model_validate(session.report)
        return ReasoningTraceRead(
            organization_id=organization_id,
            reasoning_session=ReasoningSessionRead.model_validate(session),
            stages=self._trace_stages(context=context, result=result),
            result=result,
            metadata={
                "source": "derived_reasoning_trace",
                "ephemeral": True,
                "graph_depth": graph_depth,
                "stage_count": 9,
            },
        )

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

    def _trace_stages(
        self,
        *,
        context: ReasoningContextRead,
        result: ReasoningResult,
    ) -> list[ReasoningTraceStage]:
        evidence_artifacts = [
            ReasoningTraceArtifact(
                id=evidence.id,
                title=evidence.title,
                summary=evidence.summary,
                artifact_type="evidence",
                evidence_ids=[evidence.id],
            )
            for evidence in context.evidence
        ]
        relationship_artifacts = [
            ReasoningTraceArtifact(
                id=edge.id,
                title=edge.relationship_type,
                summary=f"{edge.source_entity_id} to {edge.target_entity_id}",
                artifact_type="relationship",
                evidence_ids=edge.supporting_evidence_ids,
                relationship_ids=[edge.id],
                signal_ids=edge.supporting_signal_ids,
            )
            for edge in context.edges
        ]
        signal_artifacts = [
            ReasoningTraceArtifact(
                id=signal.id,
                title=signal.signal_type,
                summary=signal.summary,
                artifact_type="signal",
                confidence=signal.confidence,
                signal_ids=[signal.id],
            )
            for signal in context.signals
        ]
        assumption_artifacts = [
            ReasoningTraceArtifact(
                id=assumption.id,
                title=assumption.assumption_type,
                summary=assumption.statement,
                artifact_type="assumption",
                confidence=assumption.confidence,
                assumption_ids=[assumption.id],
            )
            for assumption in context.assumptions
        ]
        hypothesis_artifacts = [
            ReasoningTraceArtifact(
                id=hypothesis.id,
                title=hypothesis.status,
                summary=hypothesis.statement,
                artifact_type="hypothesis",
                confidence=hypothesis.confidence,
                evidence_ids=hypothesis.evidence_ids,
                assumption_ids=hypothesis.assumption_ids,
                hypothesis_ids=[hypothesis.id],
            )
            for hypothesis in result.hypotheses
        ]
        conflict_section = self._section(result, "conflicts")
        impact_section = self._section(result, "predicted_impacts")
        action_section = self._section(result, "recommended_actions")

        return [
            ReasoningTraceStage(
                id="collecting-evidence",
                order=1,
                title="Collecting Evidence",
                summary=f"{len(context.evidence)} evidence records selected for analysis.",
                artifacts=evidence_artifacts,
            ),
            ReasoningTraceStage(
                id="expanding-graph",
                order=2,
                title="Expanding Graph",
                summary=(
                    f"{len(context.nodes)} entities and {len(context.edges)} "
                    "relationships explored."
                ),
                artifacts=relationship_artifacts,
            ),
            ReasoningTraceStage(
                id="activating-signals",
                order=3,
                title="Activating Signals",
                summary=f"{len(context.signals)} organizational signals activated.",
                artifacts=signal_artifacts,
            ),
            ReasoningTraceStage(
                id="retrieving-assumptions",
                order=4,
                title="Retrieving Assumptions",
                summary=f"{len(context.assumptions)} persistent assumptions retrieved.",
                artifacts=assumption_artifacts,
            ),
            ReasoningTraceStage(
                id="generating-hypotheses",
                order=5,
                title="Generating Hypotheses",
                summary=f"{len(result.hypotheses)} candidate hypotheses generated.",
                artifacts=hypothesis_artifacts,
            ),
            ReasoningTraceStage(
                id="validating",
                order=6,
                title="Validating",
                summary=(
                    "Hypotheses validated against evidence, relationships, signals, "
                    "and assumptions."
                ),
                artifacts=hypothesis_artifacts,
            ),
            ReasoningTraceStage(
                id="resolving-conflicts",
                order=7,
                title="Resolving Conflicts",
                summary=conflict_section.summary if conflict_section else "No conflicts detected.",
                artifacts=[
                    ReasoningTraceArtifact(
                        id="conflict-summary",
                        title="Conflict Summary",
                        summary=(
                            conflict_section.summary
                            if conflict_section
                            else "No conflicts detected."
                        ),
                        artifact_type="conflict",
                    )
                ],
            ),
            ReasoningTraceStage(
                id="predicting-impacts",
                order=8,
                title="Predicting Impacts",
                summary=impact_section.summary if impact_section else result.answer,
                artifacts=[
                    ReasoningTraceArtifact(
                        id=finding.id,
                        title=finding.title,
                        summary=finding.summary,
                        artifact_type="prediction",
                        confidence=finding.confidence,
                        evidence_ids=finding.evidence_ids,
                        signal_ids=finding.signal_ids,
                        assumption_ids=finding.assumption_ids,
                    )
                    for finding in result.findings
                ],
            ),
            ReasoningTraceStage(
                id="planning-actions",
                order=9,
                title="Planning Actions",
                summary=(
                    action_section.summary
                    if action_section
                    else f"{len(result.recommended_actions)} actions planned."
                ),
                artifacts=[
                    ReasoningTraceArtifact(
                        id=f"action-{index}",
                        title="Recommended action",
                        summary=action,
                        artifact_type="action",
                        confidence=result.confidence,
                        evidence_ids=result.primary_evidence_ids,
                    )
                    for index, action in enumerate(result.recommended_actions, start=1)
                ],
            ),
        ]

    def _section(self, result: ReasoningResult, key: str):
        return next((section for section in result.canonical_sections if section.key == key), None)
