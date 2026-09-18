"""Statistics router."""

from fastapi import APIRouter

from src.app.database import orders_collection
from src.app.queries.statistics import (
    orders_by_status,
    revenue_by_month,
)

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)


@router.get("/orders-by-status")
def get_orders_by_status():
    """Retourne le nombre de commandes pour chaque statut.

    Returns:
        Une liste contenant chaque statut et le nombre
        de commandes correspondantes.
    """
    return orders_by_status(orders_collection)


@router.get("/revenue-by-month")
def get_revenue_by_month():
    """Retourne le chiffre d'affaires total pour chaque mois.

    Returns:
        Une liste contenant chaque mois et le chiffre
        d'affaires correspondant.
    """
    return revenue_by_month(orders_collection)
