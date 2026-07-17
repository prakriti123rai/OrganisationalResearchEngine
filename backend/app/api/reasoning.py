from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.reasoning import (
    ReasoningResult,
    ReasoningRunRead,
    ReasoningRunRequest,
    ReasoningTraceRead,
)
from app.schemas.reasoning_context import ReasoningContextRead
from app.services.exceptions import NotFoundError, ValidationError
from app.services.reasoning_engine import ReasoningEngineService, ReasoningExecutionError

router = APIRouter(tags=["reasoning"])
DatabaseSession = Annotated[Session, Depends(get_db)]
OrganizationQuery = Annotated[str, Query()]
GraphDepthQuery = Annotated[int, Query(ge=0, le=3)]


@router.post("/reason", response_model=ReasoningResult)
def reason_from_context(
    payload: ReasoningContextRead,
    db: DatabaseSession,
) -> ReasoningResult:
    service = ReasoningEngineService(db)
    try:
        return service.reason_context(context=payload)
    except ReasoningExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/reason/{reasoning_session_id}", response_model=ReasoningTraceRead)
def get_reasoning_trace(
    reasoning_session_id: str,
    db: DatabaseSession,
    organization_id: OrganizationQuery = "org-demo-apex",
    graph_depth: GraphDepthQuery = 2,
) -> ReasoningTraceRead:
    service = ReasoningEngineService(db)
    try:
        return service.get_trace(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            graph_depth=graph_depth,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "/organizations/{organization_id}/reasoning-sessions/{reasoning_session_id}/run",
    response_model=ReasoningRunRead,
)
def run_reasoning_session(
    organization_id: str,
    reasoning_session_id: str,
    payload: ReasoningRunRequest,
    db: DatabaseSession,
) -> ReasoningRunRead:
    service = ReasoningEngineService(db)
    try:
        return service.run_session(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
            graph_depth=payload.graph_depth,
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


@router.get(
    "/organizations/{organization_id}/reasoning-sessions/{reasoning_session_id}/result",
    response_model=ReasoningRunRead,
)
def get_reasoning_session_result(
    organization_id: str,
    reasoning_session_id: str,
    db: DatabaseSession,
) -> ReasoningRunRead:
    service = ReasoningEngineService(db)
    try:
        return service.get_result(
            organization_id=organization_id,
            reasoning_session_id=reasoning_session_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
