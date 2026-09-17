"""Order models."""

import math
from pydantic import BaseModel, Field, field_validator

# --- LE SOUS-MODÈLE CORRIGÉ ---


class OrderDelivery(BaseModel):
    estimated_delivery: str | None = None
    delivered_at: str | None = None

    # Ce validateur s'exécute AVANT la validation de type de Pydantic
    @field_validator("delivered_at", "estimated_delivery", mode="before")
    @classmethod
    def clean_nan_values(cls, value):
        # 1. Gère les cas où la valeur est un float NaN (provenant de Pandas/Numpy)
        if isinstance(value, float) and math.isnan(value):
            return None
        # 2. Gère les cas où la valeur est textuellement la chaîne "nan" ou "None"
        if isinstance(value, str) and value.lower() in ("nan", "none", "null"):
            return None
        return value


# --- LE RESTE DE VOS MODÈLES (Inchangés mais inclus pour le contexte) ---


class OrderItem(BaseModel):
    product_id: str
    seller_id: str
    price: float
    freight_value: float


class OrderPayment(BaseModel):
    type: str
    installments: int
    value: float


class OrderReview(BaseModel):
    review_id: str
    score: int
    comment_title: str | None = None
    comment_message: str | None = None
    creation_date: str
    answer_timestamp: str


class Order(BaseModel):
    """Modèle principal pour une commande Olist."""

    id: str = Field(alias="order_id")
    customer_id: str
    status: str
    purchase_timestamp: str
    items: list[OrderItem] = []
    payments: list[OrderPayment] = []
    reviews: list[OrderReview] = []
    delivery: OrderDelivery

    class Config:
        populate_by_name = True
