# ruff: noqa: B008

from fastapi import APIRouter, Depends, Query
from pymongo.database import Database

from src.api.dependencies import get_db
from src.services.seller_service import list_sellers

router = APIRouter(
    prefix="/sellers",
    tags=["Sellers"],
)


@router.get("")
def get_sellers(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return a paginated list of sellers."""
    return list_sellers(
        db=db,
        limit=limit,
        skip=skip,
    )