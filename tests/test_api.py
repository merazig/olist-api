"""Test les API."""

from fastapi.testclient import TestClient

from src.app.main import app


client = TestClient(app)


def test_get_customer():
    """Vérifie que l'API retourne correctement un client existant.

    Le test utilise un identifiant connu dans la base et vérifie
    que la réponse HTTP est 200.
    """
    response = client.get("/customers/06b8999e2fba1a1fbc88172c00ba8bc7")

    assert response.status_code == 200


def test_customer_not_found():
    """Vérifie que l'API retourne une erreur 404 lorsqu'un client
    demandé n'existe pas.
    """  # noqa: D205
    response = client.get("/customers/customer-inexistant")

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_orders_by_status():
    """Vérifie que l'endpoint d'agrégation des commandes par statut
    retourne une réponse HTTP 200.
    """  # noqa: D205
    response = client.get("/statistics/orders-by-status")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_revenue_by_month():
    """Vérifie que l'endpoint d'agrégation du chiffre d'affaires
    mensuel retourne une réponse HTTP 200.
    """  # noqa: D205
    response = client.get("/statistics/revenue-by-month")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
