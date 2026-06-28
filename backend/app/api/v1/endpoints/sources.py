from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sources import SourcePublic
from app.services import sources

router = APIRouter()


@router.get("", response_model=list[SourcePublic])
def list_sources(db: Session = Depends(get_db)) -> list[SourcePublic]:
    return sources.sources_overview(db)
