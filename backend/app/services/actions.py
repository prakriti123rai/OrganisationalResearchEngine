from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.action import Action
from app.models.enums import ActionStatus
from app.models.organization import Organization
from app.models.reasoning_session import ReasoningSession
from app.schemas.action import ActionPlanRead, ActionRead, ActionUpdateRequest
from app.schemas.reasoning import ReasoningFinding, ReasoningResult
from app.services.exceptions import NotFoundError, ValidationError
from app.services.reasoning_engine import ReasoningEngineService


class ActionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_actions(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
        force: bool = False,
    ) -> ActionPlanRead:
        self._require_organization(organization_id)
        reasoning_run = ReasoningEngineService(self.db).run_session(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            graph_depth=2,
            force=False,
        )
        session = self._require_reasoning_session(organization_id, reasoning_session_id)
        result = reasoning_run.result
        existing_actions = {
            action.id: action
            for action in self._list_action_records(
                organization_id=organization_id,
                reasoning_session_id=reasoning_session_id,
            )
        }

        for definition in self._action_definitions(
            organization_id=organization_id,
            reasoning_session=session,
            result=result,
        ):
            existing = existing_actions.get(definition["id"])
            if existing is None:
                self.db.add(Action(**definition))
                continue
            if force:
                existing.action_type = definition["action_type"]
                existing.title = definition["title"]
                existing.description = definition["description"]
                existing.status = ActionStatus.PROPOSED.value
                existing.confidence = definition["confidence"]
                existing.payload = definition["payload"]
                existing.approved_at = None

        self.db.commit()
        return self._plan_read(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
        )

    def approve_action(self, *, action_id: str) -> ActionRead:
        action = self._get_action(action_id)
        if action.status == ActionStatus.REJECTED.value:
            raise ValidationError(f"Rejected action '{action_id}' cannot be approved.")
        action.status = ActionStatus.APPROVED.value
        action.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(action)
        return ActionRead.model_validate(action)

    def reject_action(self, *, action_id: str) -> ActionRead:
        action = self._get_action(action_id)
        if action.status == ActionStatus.APPROVED.value:
            raise ValidationError(f"Approved action '{action_id}' cannot be rejected.")
        action.status = ActionStatus.REJECTED.value
        action.approved_at = None
        self.db.commit()
        self.db.refresh(action)
        return ActionRead.model_validate(action)

    def update_action(self, *, action_id: str, payload: ActionUpdateRequest) -> ActionRead:
        action = self._get_action(action_id)
        if action.organization_id != payload.organization_id:
            raise NotFoundError(
                f"Action '{action_id}' was not found in organization '{payload.organization_id}'."
            )
        if action.status != ActionStatus.PROPOSED.value:
            raise ValidationError("Only proposed actions can be edited.")
        if payload.title is not None:
            action.title = payload.title
        if payload.description is not None:
            action.description = payload.description
        if payload.artifact_preview is not None:
            action.payload = {
                **action.payload,
                "artifact_preview": payload.artifact_preview,
                "edited": True,
            }
        self.db.commit()
        self.db.refresh(action)
        return ActionRead.model_validate(action)

    def _action_definitions(
        self,
        *,
        organization_id: str,
        reasoning_session: ReasoningSession,
        result: ReasoningResult,
    ) -> list[dict[str, Any]]:
        evidence_ids = result.primary_evidence_ids
        high_risk_findings = [
            finding for finding in result.findings if finding.impact == "high"
        ] or result.findings
        actions = [
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="runbook_update",
                title="Update checkout incident runbook",
                description=(
                    "Revise the checkout runbook with risk timeout mitigation, fallback "
                    "alerts, and escalation steps before merge."
                ),
                preview=(
                    "Runbook delta: add Risk Engine timeout checks, fallback dashboard "
                    "links, Payments/SRE escalation, and post-merge validation steps."
                ),
                evidence_ids=self._finding_evidence(high_risk_findings, evidence_ids),
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="architecture_update",
                title="Update checkout routing architecture note",
                description=(
                    "Document that Express Checkout authorization now routes through "
                    "Risk Engine before card authorization."
                ),
                preview=(
                    "Architecture note: Checkout API -> Risk Engine -> authorization "
                    "gateway, with timeout fallback and staged rollout constraints."
                ),
                evidence_ids=evidence_ids,
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="reviewer_assignment",
                title="Assign checkout and risk reviewers",
                description=(
                    "Request review from checkout architecture and risk maintainers "
                    "before approving PR #482."
                ),
                preview=(
                    "Reviewer assignment: Maya for checkout architecture, "
                    "Noah for risk behavior."
                ),
                evidence_ids=self._finding_evidence(result.findings, evidence_ids),
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="slack_draft",
                title="Draft rollout coordination message",
                description=(
                    "Prepare a Slack announcement for Payments, Risk, and SRE covering "
                    "rollout timing, monitoring, and fallback ownership."
                ),
                preview=(
                    "Slack draft: PR #482 changes Express Checkout risk routing. "
                    "Please confirm rollout window, dashboards, fallback owner, "
                    "and reviewer coverage."
                ),
                evidence_ids=evidence_ids,
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="migration_checklist",
                title="Prepare checkout risk migration checklist",
                description=(
                    "Create a pre-merge checklist for staged rollout, timeout dashboards, "
                    "fallback validation, and post-deploy monitoring."
                ),
                preview=(
                    "Checklist: rollout flag off, risk dashboards green, fallback alert "
                    "verified, Payments/SRE sign-off, staged enablement, rollback owner."
                ),
                evidence_ids=self._finding_evidence(high_risk_findings, evidence_ids),
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="documentation_update",
                title="Update Express Checkout documentation",
                description=(
                    "Add the risk-scoring route and fallback behavior to the feature and "
                    "service documentation."
                ),
                preview=(
                    "Documentation update: Express Checkout now depends on checkout-api, "
                    "Risk Engine timeout behavior, and documented fallback handling."
                ),
                evidence_ids=evidence_ids,
            ),
            self._definition(
                organization_id=organization_id,
                reasoning_session=reasoning_session,
                result=result,
                action_type="pr_draft_summary",
                title="Draft PR approval summary",
                description=(
                    "Summarize the organizational impact, evidence, and required review "
                    "conditions for PR #482."
                ),
                preview=(
                    "PR summary: high impact, medium confidence. Merge after staged "
                    "rollout approval, risk timeout verification, and expert review."
                ),
                evidence_ids=evidence_ids,
            ),
        ]
        return actions

    def _definition(
        self,
        *,
        organization_id: str,
        reasoning_session: ReasoningSession,
        result: ReasoningResult,
        action_type: str,
        title: str,
        description: str,
        preview: str,
        evidence_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "id": self._action_id(reasoning_session.id, action_type),
            "organization_id": organization_id,
            "reasoning_session_id": reasoning_session.id,
            "action_type": action_type,
            "title": title,
            "description": description,
            "status": ActionStatus.PROPOSED.value,
            "confidence": result.confidence,
            "payload": {
                "artifact_preview": preview,
                "evidence_ids": sorted(set(evidence_ids)),
                "reasoning_session_id": reasoning_session.id,
                "impact_level": result.impact_level,
                "codex_ready": True,
                "executes_now": False,
                "requires_approval": True,
            },
        }

    def _finding_evidence(
        self,
        findings: list[ReasoningFinding],
        fallback_evidence_ids: list[str],
    ) -> list[str]:
        evidence_ids = sorted(
            {evidence_id for finding in findings for evidence_id in finding.evidence_ids}
        )
        return evidence_ids or fallback_evidence_ids

    def _action_id(self, reasoning_session_id: str, action_type: str) -> str:
        session_slug = self._slug(reasoning_session_id)
        type_slug = self._slug(action_type)
        return f"action-{session_slug}-{type_slug}"[:64]

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    def _plan_read(self, *, organization_id: str, reasoning_session_id: str) -> ActionPlanRead:
        actions = self._list_action_records(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
        )
        return ActionPlanRead(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            actions=[ActionRead.model_validate(action) for action in actions],
        )

    def _list_action_records(
        self,
        *,
        organization_id: str,
        reasoning_session_id: str,
    ) -> list[Action]:
        return list(
            self.db.scalars(
                select(Action)
                .where(
                    Action.organization_id == organization_id,
                    Action.reasoning_session_id == reasoning_session_id,
                )
                .order_by(Action.created_at.asc(), Action.id.asc())
            ).all()
        )

    def _get_action(self, action_id: str) -> Action:
        action = self.db.get(Action, action_id)
        if action is None:
            raise NotFoundError(f"Action '{action_id}' was not found.")
        return action

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization

    def _require_reasoning_session(
        self,
        organization_id: str,
        reasoning_session_id: str,
    ) -> ReasoningSession:
        session = self.db.get(ReasoningSession, reasoning_session_id)
        if session is None or session.organization_id != organization_id:
            raise NotFoundError(
                f"Reasoning session '{reasoning_session_id}' was not found in "
                f"organization '{organization_id}'."
            )
        return session
