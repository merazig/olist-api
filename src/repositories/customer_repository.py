from pymongo.database import Database


def get_customers(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return customers with pagination."""
    cursor = (
        db.customers
        .find({}, {"_id": 0})
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def get_customer_by_id(
    db: Database,
    customer_id: str,
) -> dict | None:
    """Return one customer by customer_id."""
    return db.customers.find_one(
        {"customer_id": customer_id},
        {"_id": 0},
    )


def get_customer_orders(
    db: Database,
    customer_id: str,
) -> list[dict]:
    """Return orders belonging to a customer."""
    cursor = db.orders.find(
        {"customer_id": customer_id},
        {"_id": 0},
    )

    return list(cursor)