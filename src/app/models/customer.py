"""Customer Model."""

from pydantic import BaseModel


class Customer(BaseModel):
    """Customer keys."""

    id: str
    customer_unique_id: str
    zip_code: str | None = None
    city: str | None = None
    state: str | None = None
