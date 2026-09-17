# ruff: noqa: B008

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from src.api.dependencies import get_db
from src.services.order_service import (
    find_order,
    list_orders,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)


@router.get("")
def get_orders(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return a paginated list of orders."""
    return list_orders(
        db=db,
        limit=limit,
        skip=skip,
    )


@router.get("/{order_id}")
def get_order(
    order_id: str,
    db: Database = Depends(get_db),
) -> dict:
    """Return one order by ID."""
    order = find_order(
        db=db,
        order_id=order_id,
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order