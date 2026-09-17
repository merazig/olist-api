"""Connecter à la base de données."""

import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "olist")

client = MongoClient(MONGO_URI)

db = client[MONGO_DB]

customers_collection = db["customers"]
products_collection = db["products"]
orders_collection = db["orders"]
sellers_collection = db["sellers"]
