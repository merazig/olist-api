from pymongo.database import Database

from src.repositories.order_repository import (
    get_order_by_id,
    get_orders,
)


def list_orders(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return a paginated list of orders."""
    return get_orders(
        db=db,
        limit=limit,
        skip=skip,
    )


def find_order(
    db: Database,
    order_id: str,
) -> dict | None:
    """Return an order by ID."""
    return get_order_by_id(
        db=db,
        order_id=order_id,
    )