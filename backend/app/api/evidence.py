from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.evidence import EvidenceCreate, EvidenceRead
from app.services.evidence import EvidenceConflictError, EvidenceNotFoundError, EvidenceService
from app.services.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/organizations/{organization_id}/evidence", tags=["evidence"])
DatabaseSession = Annotated[Session, Depends(get_db)]
LimitQuery = Annotated[int, Query(ge=1, le=200)]
OffsetQuery = Annotated[int, Query(ge=0)]


@router.get("", response_model=list[EvidenceRead])
def list_evidence(
    organization_id: str,
    db: DatabaseSession,
    evidence_type: Optional[str] = None,
    source: Optional[str] = None,
    author_id: Optional[str] = None,
    entity_id: Optional[str] = None,
    relationship_id: Optional[str] = None,
    signal_id: Optional[str] = None,
    assumption_id: Optional[str] = None,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[EvidenceRead]:
    service = EvidenceService(db)
    try:
        return service.list_evidence(
            organization_id=organization_id,
            evidence_type=evidence_type,
            source=source,
            author_id=author_id,
            entity_id=entity_id,
            relationship_id=relationship_id,
            signal_id=signal_id,
            assumption_id=assumption_id,
            limit=limit,
            offset=offset,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
def create_evidence(
    organization_id: str,
    payload: EvidenceCreate,
    db: DatabaseSession,
) -> EvidenceRead:
    service = EvidenceService(db)
    try:
        return service.create_evidence(organization_id=organization_id, payload=payload)
    except EvidenceConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    organization_id: str,
    evidence_id: str,
    db: DatabaseSession,
) -> EvidenceRead:
    service = EvidenceService(db)
    try:
        return service.get_evidence(organization_id=organization_id, evidence_id=evidence_id)
    except EvidenceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
