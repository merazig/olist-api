"""Orders router."""

from fastapi import APIRouter, HTTPException, Query

from src.app.database import orders_collection
from src.app.models.order import Order


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=list[Order])
def get_orders(
    status: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
):
    """All orders."""
    query = {}

    if status:
        query["status"] = status

    orders = orders_collection.find(query).skip(skip).limit(limit)

    result = []

    for order in orders:
        order["id"] = order.pop("_id")
        result.append(order)

    return result


@router.get("/{order_id}", response_model=Order)
def get_order(order_id: str):
    """One order."""
    order = orders_collection.find_one({"_id": order_id})

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    order["id"] = order.pop("_id")

    return order
