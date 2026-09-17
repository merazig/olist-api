"""Produt model."""

from pydantic import BaseModel, Field


class ProductDimensions(BaseModel):
    """Sous-modèle pour les dimensions du produit."""

    length_cm: float | None = None
    height_cm: float | None = None
    width_cm: float | None = None


class Product(BaseModel):
    """Modèle principal pour le produit."""

    # Utilisation de Field pour mapper '_id' de MongoDB vers l'attribut 'id'
    id: str = Field(alias="product_id")

    category: str | None = None
    name_length: int | None = None
    description_length: int | None = None
    photos_qty: int | None = None
    weight_g: float | None = None

    # Intégration du sous-modèle imbriqué
    dimensions: ProductDimensions | None = None

    class Config:
        """Permet à FastAPI et Pydantic de lire le modèle
        en utilisant aussi bien 'id' que '_id'.
        """  # noqa: D205

        populate_by_name = True
