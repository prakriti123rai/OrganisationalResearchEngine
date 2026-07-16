from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.graph import GraphSyncRead, OrganizationalGraphRead
from app.services.exceptions import NotFoundError, ValidationError
from app.services.organizational_graph import GraphSyncError, OrganizationalGraphService

router = APIRouter(prefix="/organizations/{organization_id}/graph", tags=["graph"])
DatabaseSession = Annotated[Session, Depends(get_db)]
LimitQuery = Annotated[int, Query(ge=1, le=500)]
OffsetQuery = Annotated[int, Query(ge=0)]


@router.get("", response_model=OrganizationalGraphRead)
def get_organizational_graph(
    organization_id: str,
    db: DatabaseSession,
    entity_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    active_only: bool = True,
    limit: LimitQuery = 200,
    offset: OffsetQuery = 0,
) -> OrganizationalGraphRead:
    service = OrganizationalGraphService(db)
    try:
        return service.get_graph(
            organization_id=organization_id,
            entity_type=entity_type,
            relationship_type=relationship_type,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post("/sync", response_model=GraphSyncRead)
def sync_organizational_graph(
    organization_id: str,
    db: DatabaseSession,
) -> GraphSyncRead:
    service = OrganizationalGraphService(db)
    try:
        return service.sync_to_neo4j(organization_id=organization_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except GraphSyncError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/neo4j", response_model=OrganizationalGraphRead)
def get_neo4j_organizational_graph(
    organization_id: str,
    db: DatabaseSession,
    entity_type: Optional[str] = None,
    relationship_type: Optional[str] = None,
    active_only: bool = True,
    limit: LimitQuery = 200,
    offset: OffsetQuery = 0,
) -> OrganizationalGraphRead:
    service = OrganizationalGraphService(db)
    try:
        return service.get_neo4j_graph(
            organization_id=organization_id,
            entity_type=entity_type,
            relationship_type=relationship_type,
            active_only=active_only,
            limit=limit,
            offset=offset,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
