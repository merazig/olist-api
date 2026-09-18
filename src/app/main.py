"""API main."""

from fastapi import FastAPI

from src.app.routers import customers, orders, products, sellers, statistics

app = FastAPI(
    title="Olist API",
    description="API REST permettant d'accéder aux données e-commerce Olist",
    version="1.0.0",
)

app.include_router(customers.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(sellers.router)
app.include_router(statistics.router)


@app.get("/")
def root():
    """API root."""
    return {"message": "Olist API is running"}
