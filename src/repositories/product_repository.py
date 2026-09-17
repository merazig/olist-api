from pymongo.database import Database


def get_products(
    db: Database,
    limit: int = 20,
    skip: int = 0,
) -> list[dict]:
    """Return products with pagination."""
    cursor = (
        db.products
        .find({}, {"_id": 0})
        .skip(skip)
        .limit(limit)
    )

    return list(cursor)


def get_product_by_id(
    db: Database,
    product_id: str,
) -> dict | None:
    """Return one product by product_id."""
    return db.products.find_one(
        {"product_id": product_id},
        {"_id": 0},
    )