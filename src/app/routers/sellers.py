"""Sellers router."""

from fastapi import APIRouter, HTTPException, Query

from src.app.database import sellers_collection
from src.app.models.seller import Seller


router = APIRouter(prefix="/sellers", tags=["Sellers"])


@router.get("", response_model=list[Seller])
def get_sellers(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """All sellers."""
    sellers = sellers_collection.find({}).skip(skip).limit(limit)

    result = []

    for seller in sellers:
        seller["id"] = seller.pop("_id")
        result.append(seller)

    return result


@router.get("/{seller_id}", response_model=Seller)
def get_seller(seller_id: str):
    """One seller."""
    seller = sellers_collection.find_one({"_id": seller_id})

    if seller is None:
        raise HTTPException(status_code=404, detail="Seller not found")

    seller["id"] = seller.pop("_id")

    return seller
