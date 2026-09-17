# ruff: noqa: B008

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from src.api.dependencies import get_db
from src.services.review_service import list_reviews

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get("")
def get_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return a paginated list of reviews."""
    return list_reviews(
        db=db,
        limit=limit,
        skip=skip,
    )