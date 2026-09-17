# ruff: noqa: B008

from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from src.api.dependencies import get_db
from src.services.product_service import (
    find_product,
    list_products,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get("")
def get_products(
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    db: Database = Depends(get_db),
) -> list[dict]:
    """Return a paginated list of products."""
    return list_products(
        db=db,
        limit=limit,
        skip=skip,
    )


@router.get("/{product_id}")
def get_product(
    product_id: str,
    db: Database = Depends(get_db),
) -> dict:
    """Return one product by ID."""
    product = find_product(
        db=db,
        product_id=product_id,
    )

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return product