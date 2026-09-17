from pymongo import MongoClient

from src.config import MONGO_DATABASE, MONGO_URI


def get_client() -> MongoClient:
    """Create a MongoDB client."""
    return MongoClient(MONGO_URI)


def get_database():
    """Return the Olist MongoDB database."""
    client = get_client()
    return client[MONGO_DATABASE]
