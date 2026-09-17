from pymongo.database import Database


def get_orders(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return orders with pagination."""
    cursor = (
        db.orders
        .find({}, {"_id": 0})
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def get_order_by_id(
    db: Database,
    order_id: str,
) -> dict | None:
    """Return one order by order_id."""
    return db.orders.find_one(
        {"order_id": order_id},
        {"_id": 0},
    )