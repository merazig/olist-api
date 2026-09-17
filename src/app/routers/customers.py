"""Customer router."""

from fastapi import APIRouter, HTTPException, Query

from src.app.database import customers_collection, orders_collection
from src.app.models.customer import Customer


router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=list[Customer])
def get_customers(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """All customers."""
    customers = customers_collection.find({}).skip(skip).limit(limit)

    result = []

    for customer in customers:
        customer["id"] = customer.pop("_id")

        result.append(customer)

    return result


@router.get("/{customer_id}", response_model=Customer)
def get_customer(customer_id: str):
    """One customer."""
    customer = customers_collection.find_one({"_id": customer_id})

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer["id"] = customer.pop("_id")

    return customer


@router.get("/{customer_id}/orders")
def get_customer_orders(
    customer_id: str, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
):
    """Customer orders."""
    customer = customers_collection.find_one({"_id": customer_id})

    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = orders_collection.find({"customer_id": customer_id}).skip(skip).limit(limit)

    result = []

    for order in orders:
        order["id"] = order.pop("_id")
        result.append(order)

    return result
