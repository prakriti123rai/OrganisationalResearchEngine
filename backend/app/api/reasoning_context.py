from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.reasoning_context import ReasoningContextRead
from app.services.exceptions import NotFoundError, ValidationError
from app.services.reasoning_context import ReasoningContextService

router = APIRouter(prefix="/organizations/{organization_id}", tags=["reasoning-context"])
DatabaseSession = Annotated[Session, Depends(get_db)]
GraphDepthQuery = Annotated[int, Query(ge=0, le=3)]


@router.get(
    "/reasoning-sessions/{reasoning_session_id}/context",
    response_model=ReasoningContextRead,
)
def get_reasoning_session_context(
    organization_id: str,
    reasoning_session_id: str,
    db: DatabaseSession,
    graph_depth: GraphDepthQuery = 2,
) -> ReasoningContextRead:
    service = ReasoningContextService(db)
    try:
        return service.build_for_session(
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


@router.get(
    "/pull-requests/{pull_request_id}/context",
    response_model=ReasoningContextRead,
)
def get_pull_request_context(
    organization_id: str,
    pull_request_id: str,
    db: DatabaseSession,
    question: Optional[str] = None,
    pattern: Optional[str] = "pull_request_impact",
    graph_depth: GraphDepthQuery = 2,
) -> ReasoningContextRead:
    service = ReasoningContextService(db)
    try:
        return service.build_for_pull_request(
            organization_id=organization_id,
            pull_request_id=pull_request_id,
            question=question,
            pattern=pattern,
            graph_depth=graph_depth,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
