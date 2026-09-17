"""Seller Model."""

from pydantic import BaseModel


class Seller(BaseModel):
    """Seller keys."""

    id: str
    zip_code: int | None = None
    city: str | None = None
    state: str | None = None
