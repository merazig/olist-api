from fastapi import FastAPI
from pymongo.errors import PyMongoError

from src.api.routes.customers import router as customers_router
from src.api.routes.orders import router as orders_router
from src.api.routes.products import router as products_router
from src.api.routes.reviews import router as reviews_router
from src.api.routes.sellers import router as sellers_router
from src.database.connection import get_database

app = FastAPI(
    title="Olist API",
    description="API REST pour les donnees e-commerce Olist",
    version="1.0.0",
)
app.include_router(customers_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(sellers_router)
app.include_router(reviews_router)

@app.get("/")
def root():
    """Return API information."""
    return {
        "message": "Olist API",
        "status": "running",
    }


@app.get("/health")
def health():
    """Check API and MongoDB health."""
    try:
        db = get_database()
        db.command("ping")

        return {
            "status": "healthy",
            "mongodb": "connected",
        }
    except PyMongoError:
        return {
            "status": "unhealthy",
            "mongodb": "disconnected",
        }
    finally:
        try:
            db.client.close()
        except UnboundLocalError:
            pass