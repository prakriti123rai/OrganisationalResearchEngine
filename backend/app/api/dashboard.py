from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.dashboard import DashboardRead
from app.schemas.organization import OrganizationRead
from app.services.dashboard import DashboardService
from app.services.exceptions import NotFoundError

router = APIRouter(tags=["dashboard"])
DatabaseSession = Annotated[Session, Depends(get_db)]
OrganizationQuery = Annotated[str, Query()]


@router.get("/dashboard", response_model=DashboardRead)
def get_dashboard(
    db: DatabaseSession,
    organization_id: OrganizationQuery = "org-demo-apex",
) -> DashboardRead:
    service = DashboardService(db)
    try:
        return service.get_dashboard(organization_id=organization_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/organization", response_model=OrganizationRead)
def get_organization(
    db: DatabaseSession,
    organization_id: OrganizationQuery = "org-demo-apex",
) -> OrganizationRead:
    service = DashboardService(db)
    try:
        return service.get_organization(organization_id=organization_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
