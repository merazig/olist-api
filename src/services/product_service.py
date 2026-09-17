from pymongo.database import Database

from src.repositories.product_repository import (
    get_product_by_id,
    get_products,
)


def list_products(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return a paginated list of products."""
    return get_products(
        db=db,
        limit=limit,
        skip=skip,
    )


def find_product(
    db: Database,
    product_id: str,
) -> dict | None:
    """Return a product by ID."""
    return get_product_by_id(
        db=db,
        product_id=product_id,
    )