from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.execution.codex_adapter import CodexAdapter
from app.models.action import Action
from app.models.enums import ActionStatus, ExecutionStatus
from app.models.execution_history import ExecutionHistory
from app.models.organization import Organization
from app.schemas.execution_history import ExecutionHistoryList, ExecutionHistoryRead
from app.services.exceptions import NotFoundError, ValidationError


class ExecutionService:
    def __init__(self, db: Session, codex_adapter: CodexAdapter | None = None) -> None:
        self.db = db
        self.codex_adapter = codex_adapter or CodexAdapter()

    def start_execution(self, *, organization_id: str, action_id: str) -> ExecutionHistoryRead:
        self._require_organization(organization_id)
        action = self._require_action(organization_id=organization_id, action_id=action_id)
        if action.status not in {
            ActionStatus.APPROVED.value,
            ActionStatus.EXECUTED.value,
        }:
            raise ValidationError("Only approved actions can be executed.")

        existing = self._get_execution_for_action(action_id)
        if existing is not None:
            if action.status != ActionStatus.EXECUTED.value:
                action.status = ActionStatus.EXECUTED.value
                self.db.commit()
                self.db.refresh(existing)
            return ExecutionHistoryRead.model_validate(existing)

        execution = ExecutionHistory(
            id=self._execution_id(action.id),
            organization_id=organization_id,
            action_id=action.id,
            status=ExecutionStatus.RUNNING.value,
            artifact_type=None,
            artifact_title=None,
            logs="Execution queued after human approval.",
            result_metadata={
                "production_changes": False,
                "mock_execution": True,
            },
        )
        self.db.add(execution)
        self.db.flush()

        result = self.codex_adapter.execute(action)
        artifact = result.artifact
        execution.status = ExecutionStatus.COMPLETED.value
        execution.artifact_type = artifact.artifact_type
        execution.artifact_title = artifact.artifact_title
        execution.logs = "\n".join(result.logs)
        execution.result_metadata = {
            **artifact.metadata,
            "artifact_content": artifact.content,
            "mock_execution": True,
            "codex_ready": True,
        }
        execution.completed_at = datetime.now(timezone.utc)
        action.status = ActionStatus.EXECUTED.value
        self.db.commit()
        self.db.refresh(execution)
        return ExecutionHistoryRead.model_validate(execution)

    def get_execution(
        self,
        *,
        execution_id: str,
        organization_id: str | None = None,
    ) -> ExecutionHistoryRead:
        execution = self.db.get(ExecutionHistory, execution_id)
        if execution is None or (
            organization_id is not None and execution.organization_id != organization_id
        ):
            raise NotFoundError(f"Execution '{execution_id}' was not found.")
        return ExecutionHistoryRead.model_validate(execution)

    def list_history(
        self,
        *,
        organization_id: str,
        limit: int = 50,
    ) -> ExecutionHistoryList:
        self._require_organization(organization_id)
        executions = list(
            self.db.scalars(
                select(ExecutionHistory)
                .where(ExecutionHistory.organization_id == organization_id)
                .order_by(ExecutionHistory.started_at.desc(), ExecutionHistory.id.asc())
                .limit(limit)
            ).all()
        )
        return ExecutionHistoryList(
            organization_id=organization_id,
            executions=[ExecutionHistoryRead.model_validate(execution) for execution in executions],
        )

    def _get_execution_for_action(self, action_id: str) -> ExecutionHistory | None:
        return self.db.scalar(
            select(ExecutionHistory)
            .where(ExecutionHistory.action_id == action_id)
            .order_by(ExecutionHistory.started_at.desc(), ExecutionHistory.id.asc())
        )

    def _require_organization(self, organization_id: str) -> Organization:
        organization = self.db.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(f"Organization '{organization_id}' was not found.")
        return organization

    def _require_action(self, *, organization_id: str, action_id: str) -> Action:
        action = self.db.get(Action, action_id)
        if action is None or action.organization_id != organization_id:
            raise NotFoundError(
                f"Action '{action_id}' was not found in organization '{organization_id}'."
            )
        return action

    def _execution_id(self, action_id: str) -> str:
        action_slug = re.sub(r"[^a-z0-9]+", "-", action_id.lower()).strip("-")
        return f"execution-{action_slug}"[:64]
