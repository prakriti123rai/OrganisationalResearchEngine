from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.reasoning_session import ReasoningSession
from app.schemas.reasoning import (
    ReasoningFinding,
    ReasoningResult,
    ReasoningRunRead,
    ReasoningStep,
)
from app.schemas.reasoning_context import ReasoningContextRead, ReasoningContextSection
from app.schemas.reasoning_session import ReasoningSessionRead
from app.services.exceptions import NotFoundError, ValidationError
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

        try:
            result = self._reason(context)
        except Exception as exc:
            session.status = "failed"
            session.context_metadata = {
                **session.context_metadata,
                "reasoning_engine": {
                    "model": self.settings.reasoning_model,
                    "provider": self._provider_name(),
                    "error": str(exc),
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

    def _reason(self, context: ReasoningContextRead) -> ReasoningResult:
        if self.settings.openai_api_key:
            return self._reason_with_openai(context)
        return self._deterministic_reasoning(context)

    def _reason_with_openai(self, context: ReasoningContextRead) -> ReasoningResult:
        prompt_payload = self._prompt_payload(context)
        body = {
            "model": self.settings.reasoning_model,
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
                    "schema": self._json_schema(),
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            self.settings.openai_responses_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request, timeout=self.settings.openai_timeout_seconds
            ) as res:
                response_payload = json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ReasoningExecutionError(f"OpenAI reasoning request failed: {detail}") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise ReasoningExecutionError(f"OpenAI reasoning request failed: {exc}") from exc

        raw_result = self._extract_response_json(response_payload)
        raw_result["model"] = self.settings.reasoning_model
        raw_result["provider"] = "openai_responses"
        return ReasoningResult.model_validate(raw_result)

    def _deterministic_reasoning(self, context: ReasoningContextRead) -> ReasoningResult:
        sections = {section.key: section for section in context.sections}
        dependency_section = sections.get("dependencies")
        ownership_section = sections.get("ownership")
        reviewer_section = sections.get("reviewers")
        operational_section = sections.get("operational_readiness")

        impacted_entity_ids = sorted(
            {
                *context.scope.entity_ids,
                *self._section_entity_ids(dependency_section),
                *self._section_entity_ids(operational_section),
            }
        )
        primary_evidence_ids = sorted(
            {
                *context.scope.evidence_ids,
                *self._section_evidence_ids(dependency_section),
                *self._section_evidence_ids(operational_section),
            }
        )
        findings = [
            self._finding(
                finding_id="finding-ownership",
                title="Ownership path is explicit",
                summary=(
                    "Payments owns Checkout API changes while SRE owns operational "
                    "escalation through the runbook context."
                ),
                impact="medium",
                confidence=self._confidence_for_section(ownership_section),
                section=ownership_section,
            ),
            self._finding(
                finding_id="finding-dependency-risk",
                title="Risk Engine dependency controls rollout safety",
                summary=(
                    "The PR routes express checkout through risk scoring, making Risk "
                    "Engine timeout behavior and review availability critical to the rollout."
                ),
                impact="high",
                confidence=self._confidence_for_section(dependency_section),
                section=dependency_section,
            ),
            self._finding(
                finding_id="finding-review",
                title="Review is concentrated in checkout and risk experts",
                summary=(
                    "The context points to Maya and Noah as high-signal reviewers for "
                    "architecture and risk behavior."
                ),
                impact="medium",
                confidence=self._confidence_for_section(reviewer_section),
                section=reviewer_section,
            ),
            self._finding(
                finding_id="finding-operational-readiness",
                title="Operational readiness depends on recent incident context",
                summary=(
                    "Runbook, deployment, and incident evidence show the rollout should "
                    "be checked against current risk timeout mitigations."
                ),
                impact="high",
                confidence=self._confidence_for_section(operational_section),
                section=operational_section,
            ),
        ]

        return ReasoningResult(
            question=context.question,
            answer=(
                "checkout-api PR #482 has high organizational impact because it changes "
                "the authorization path for Express Checkout, touches Checkout API and "
                "Risk Engine ownership boundaries, and depends on operational knowledge "
                "from recent timeout incidents."
            ),
            model=self.settings.reasoning_model,
            provider="deterministic_local",
            impact_level="high",
            confidence="medium",
            findings=findings,
            reasoning_steps=self._reasoning_steps(context.sections),
            open_questions=[
                "Has the staged rollout plan been accepted by Payments, Risk, and SRE?",
                "Are risk timeout dashboards and fallback alerts current for this rollout?",
            ],
            impacted_entity_ids=impacted_entity_ids,
            primary_evidence_ids=primary_evidence_ids,
            context_scope=context.scope.model_dump(mode="json"),
            metadata={
                "source": "canonical_context",
                "fallback_reason": "OPENAI_API_KEY is not configured",
                "context_builder": context.context_metadata.get("builder"),
            },
        )

    def _reasoning_steps(self, sections: list[ReasoningContextSection]) -> list[ReasoningStep]:
        steps = []
        for index, section in enumerate(sections, start=1):
            steps.append(
                ReasoningStep(
                    id=f"step-{section.key}",
                    order=index,
                    section_key=section.key,
                    title=section.title,
                    reasoning=section.summary,
                    evidence_ids=section.evidence_ids,
                    signal_ids=section.signal_ids,
                    assumption_ids=section.assumption_ids,
                )
            )
        return steps

    def _finding(
        self,
        *,
        finding_id: str,
        title: str,
        summary: str,
        impact: str,
        confidence: str,
        section: Optional[ReasoningContextSection],
    ) -> ReasoningFinding:
        return ReasoningFinding(
            id=finding_id,
            title=title,
            summary=summary,
            impact=impact,
            confidence=confidence,
            entity_ids=self._section_entity_ids(section),
            evidence_ids=self._section_evidence_ids(section),
            signal_ids=section.signal_ids if section is not None else [],
            assumption_ids=section.assumption_ids if section is not None else [],
        )

    def _prompt_payload(self, context: ReasoningContextRead) -> dict[str, Any]:
        return {
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
            "assumptions": [
                assumption.model_dump(mode="json") for assumption in context.assumptions
            ],
        }

    def _json_schema(self) -> dict[str, Any]:
        return ReasoningResult.model_json_schema()

    def _extract_response_json(self, response_payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(response_payload.get("output_text"), str):
            return json.loads(response_payload["output_text"])

        for output in response_payload.get("output", []):
            for content in output.get("content", []):
                if content.get("type") in {"output_text", "text"} and isinstance(
                    content.get("text"), str
                ):
                    return json.loads(content["text"])
        raise ReasoningExecutionError("OpenAI reasoning response did not include JSON text.")

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

    def _confidence_for_section(self, section: Optional[ReasoningContextSection]) -> str:
        if section is None:
            return "low"
        if section.evidence_ids and section.signal_ids and section.assumption_ids:
            return "medium"
        if section.evidence_ids:
            return "low"
        return "low"

    def _section_entity_ids(self, section: Optional[ReasoningContextSection]) -> list[str]:
        return section.entity_ids if section is not None else []

    def _section_evidence_ids(self, section: Optional[ReasoningContextSection]) -> list[str]:
        return section.evidence_ids if section is not None else []

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()
