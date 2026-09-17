"""Charge les données transformées dans une base mongo."""
import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


def get_database():
    """Connect to database."""
    mongo_uri = os.getenv("MONGO_URI")
    mongo_db = os.getenv("MONGO_DB")

    if not mongo_uri or not mongo_db:
        raise ValueError("MongoDB configuration missing in .env")

    client = MongoClient(mongo_uri)

    client.admin.command("ping")

    print("MongoDB connecté !")

    return client[mongo_db]


def load_to_mongo(db, collection_name, data):
    """Load to mongo."""
    collection = db[collection_name]

    collection.delete_many({})

    if not data:
        print(f"{collection_name}: aucune donnée à insérer")
        return

    result = collection.insert_many(data)

    print(
        f"{collection_name}: "
        f"{len(result.inserted_ids)} documents insérés"
    )
