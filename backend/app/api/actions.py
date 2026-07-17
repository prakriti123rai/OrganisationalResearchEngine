from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.action import (
    ActionGenerateRequest,
    ActionPlanRead,
    ActionRead,
    ActionUpdateRequest,
)
from app.services.actions import ActionService
from app.services.exceptions import NotFoundError, ValidationError
from app.services.reasoning_engine import ReasoningExecutionError

router = APIRouter(prefix="/actions", tags=["actions"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/generate", response_model=ActionPlanRead)
def generate_actions(
    payload: ActionGenerateRequest,
    db: DatabaseSession,
) -> ActionPlanRead:
    service = ActionService(db)
    try:
        return service.generate_actions(
            organization_id=payload.organization_id,
            reasoning_session_id=payload.reasoning_session_id,
            force=payload.force,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ReasoningExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.patch("/{action_id}", response_model=ActionRead)
def update_action(
    action_id: str,
    payload: ActionUpdateRequest,
    db: DatabaseSession,
) -> ActionRead:
    service = ActionService(db)
    try:
        return service.update_action(action_id=action_id, payload=payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{action_id}/approve", response_model=ActionRead)
def approve_action(action_id: str, db: DatabaseSession) -> ActionRead:
    service = ActionService(db)
    try:
        return service.approve_action(action_id=action_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/{action_id}/reject", response_model=ActionRead)
def reject_action(action_id: str, db: DatabaseSession) -> ActionRead:
    service = ActionService(db)
    try:
        return service.reject_action(action_id=action_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
