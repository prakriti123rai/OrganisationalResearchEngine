from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.execution.execution_service import ExecutionService
from app.schemas.execution_history import (
    ExecutionHistoryList,
    ExecutionHistoryRead,
    ExecutionStartRequest,
)
from app.services.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/execution", tags=["execution"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post("/start", response_model=ExecutionHistoryRead)
def start_execution(
    payload: ExecutionStartRequest,
    db: DatabaseSession,
) -> ExecutionHistoryRead:
    service = ExecutionService(db)
    try:
        return service.start_execution(
            organization_id=payload.organization_id,
            action_id=payload.action_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/history", response_model=ExecutionHistoryList)
def list_execution_history(
    db: DatabaseSession,
    organization_id: str = "org-demo-apex",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> ExecutionHistoryList:
    service = ExecutionService(db)
    try:
        return service.list_history(organization_id=organization_id, limit=limit)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{execution_id}", response_model=ExecutionHistoryRead)
def get_execution(
    execution_id: str,
    db: DatabaseSession,
    organization_id: str | None = None,
) -> ExecutionHistoryRead:
    service = ExecutionService(db)
    try:
        return service.get_execution(
            execution_id=execution_id,
            organization_id=organization_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
