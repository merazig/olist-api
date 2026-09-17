id="61843"
# ruff: noqa: B008

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from src.api.dependencies import get_db
from src.services.customer_service import (
    find_customer,
    list_customer_orders,
    list_customers,
)

router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("")
def get_customers(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return a paginated list of customers."""
    return list_customers(
        db=db,
        limit=limit,
        skip=skip,
    )


@router.get("/{customer_id}/orders")
def get_customer_orders(
    customer_id: str,
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return orders belonging to a customer."""
    return list_customer_orders(
        db=db,
        customer_id=customer_id,
    )


@router.get("/{customer_id}")
def get_customer(
    customer_id: str,
    db: Database = Depends(get_db),
) -> dict:
    """Return one customer by ID."""
    customer = find_customer(
        db=db,
        customer_id=customer_id,
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return customer
