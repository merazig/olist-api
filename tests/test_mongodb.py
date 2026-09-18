"""Teste la base mongo."""

from src.app.database import db


def test_database_connection():
    """Vérifie que l'application peut communiquer avec MongoDB.

    Le test envoie une commande ping au serveur MongoDB.
    """
    result = db.command("ping")

    assert result["ok"] == 1


def test_orders_collection_exists():
    """Vérifie que la collection `orders` existe dans MongoDB."""
    collections = db.list_collection_names()

    assert "orders" in collections


def test_customer_id_index_exists():
    """Vérifie qu'un index est présent sur `customer_id`
    dans la collection `orders`.
    """  # noqa: D205
    indexes = db.orders.index_information()

    assert "customer_id_1" in indexes
