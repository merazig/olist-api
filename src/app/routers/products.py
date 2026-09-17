"""Products routers."""

from fastapi import APIRouter, HTTPException, Query

from src.app.database import products_collection
from src.app.models.product import Product


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=list[Product])
def get_products(
    category: str | None = None, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
):
    """All Products."""
    query = {}

    if category:
        query["category"] = category

    products = products_collection.find(query).skip(skip).limit(limit)

    result = []

    for product in products:
        product["id"] = product.pop("_id")
        result.append(product)

    return result


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str):
    """One product."""
    product = products_collection.find_one({"_id": product_id})

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    product["id"] = product.pop("_id")

    return product
