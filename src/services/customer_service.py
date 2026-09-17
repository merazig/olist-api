from pymongo.database import Database

from src.repositories.customer_repository import (
    get_customer_by_id,
    get_customer_orders,
    get_customers,
)


def list_customers(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return a paginated list of customers."""
    return get_customers(
        db=db,
        limit=limit,
        skip=skip,
    )


def find_customer(
    db: Database,
    customer_id: str,
) -> dict | None:
    """Return a customer by ID."""
    return get_customer_by_id(
        db=db,
        customer_id=customer_id,
    )


def list_customer_orders(
    db: Database,
    customer_id: str,
) -> list[dict]:
    """Return orders belonging to a customer."""
    return get_customer_orders(
        db=db,
        customer_id=customer_id,
    )
