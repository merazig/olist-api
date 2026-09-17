from src.database.connection import get_database


def get_db():
    """Provide the MongoDB database to FastAPI routes."""
    db = get_database()

    try:
        yield db
    finally:
        db.client.close()
