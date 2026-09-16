import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

# ============================================================
# CONFIGURATION
# ============================================================

PROCESSED_DIR = Path("data/processed")
BATCH_SIZE = 1000

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017",
)

MONGO_DATABASE = os.getenv(
    "MONGO_DATABASE",
    "olist",
)


# ============================================================
# CONNEXION MONGODB
# ============================================================

def get_database():
    """Établit et vérifie la connexion à MongoDB."""
    client = MongoClient(MONGO_URI)

    client.admin.command("ping")

    print("Connexion MongoDB réussie.")

    return client, client[MONGO_DATABASE]


# ============================================================
# UTILITAIRES
# ============================================================

def parse_date(value):
    """Convertit une valeur en datetime Python ou retourne None."""
    if pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.to_pydatetime()


def clean_value(value):
    """Convertit les valeurs pandas manquantes en None."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def clean_zip_code(value) -> str | None:
    """
    Normalise un code postal sur 5 caractères.

    Le code postal est traité comme une chaîne et non comme
    un nombre afin de conserver les zéros initiaux.
    """
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = value.removesuffix(".0")

    return value.zfill(5)


# ============================================================
# CUSTOMERS
# ============================================================

def load_customers(db) -> None:
    """Charge les clients MongoDB par lots."""
    path = PROCESSED_DIR / "customers.csv"
    collection = db.customers

    total = 0

    print("Chargement des clients par lots...")

    for chunk in pd.read_csv(
        path,
        dtype={
            "customer_id": "string",
            "customer_unique_id": "string",
            "customer_zip_code_prefix": "string",
            "customer_city": "string",
            "customer_state": "string",
        },
        chunksize=BATCH_SIZE,
    ):
        operations = []

        for row in chunk.to_dict("records"):
            document = {
                "customer_id": clean_value(
                    row["customer_id"]
                ),
                "customer_unique_id": clean_value(
                    row["customer_unique_id"]
                ),
                "location": {
                    "zip_code_prefix": clean_zip_code(
                        row["customer_zip_code_prefix"]
                    ),
                    "city": (
                        str(row["customer_city"])
                        .strip()
                        .lower()
                        if pd.notna(row["customer_city"])
                        else ""
                    ),
                    "state": (
                        str(row["customer_state"])
                        .strip()
                        .upper()
                        if pd.notna(row["customer_state"])
                        else ""
                    ),
                },
            }

            operations.append(
                UpdateOne(
                    {"customer_id": document["customer_id"]},
                    {"$set": document},
                    upsert=True,
                )
            )

        if operations:
            collection.bulk_write(
                operations,
                ordered=False,
            )

        total += len(operations)

        print(f"  Clients chargés : {total:,}")

    print(f"Clients chargés : {total:,}")


# ============================================================
# PRODUCTS
# ============================================================

def load_products(db) -> None:
    """Charge les produits et leurs traductions dans MongoDB."""
    products_path = PROCESSED_DIR / "products.csv"
    translation_path = (
        PROCESSED_DIR / "category_translation.csv"
    )

    products_df = pd.read_csv(products_path)

    translations_df = pd.read_csv(
        translation_path,
        dtype="string",
    )

    translations = dict(
        zip(
            translations_df["product_category_name"],
            translations_df["product_category_name_english"],
        )
    )

    operations = []

    for row in products_df.to_dict("records"):
        category_name = clean_value(
            row["product_category_name"]
        )

        category_name_en = translations.get(
            category_name
        )

        if category_name == "unknown":
            category_name_en = "unknown"

        document = {
            "product_id": clean_value(
                row["product_id"]
            ),
            "category": {
                "name": category_name,
                "name_en": clean_value(
                    category_name_en
                ),
            },
            "attributes": {
                "name_length": clean_value(
                    row["product_name_lenght"]
                ),
                "description_length": clean_value(
                    row["product_description_lenght"]
                ),
                "photos_qty": clean_value(
                    row["product_photos_qty"]
                ),
            },
            "dimensions": {
                "weight_g": clean_value(
                    row["product_weight_g"]
                ),
                "length_cm": clean_value(
                    row["product_length_cm"]
                ),
                "height_cm": clean_value(
                    row["product_height_cm"]
                ),
                "width_cm": clean_value(
                    row["product_width_cm"]
                ),
            },
        }

        operations.append(
            UpdateOne(
                {"product_id": document["product_id"]},
                {"$set": document},
                upsert=True,
            )
        )

    if operations:
        db.products.bulk_write(
            operations,
            ordered=False,
        )

    print(f"Products chargés : {len(operations)}")
    print(
        f"Traductions de catégories : "
        f"{len(translations)}"
    )


# ============================================================
# SELLERS
# ============================================================

def load_sellers(db) -> None:
    """Charge les vendeurs dans la collection sellers."""
    path = PROCESSED_DIR / "sellers.csv"

    df = pd.read_csv(
        path,
        dtype={
            "seller_id": "string",
            "seller_zip_code_prefix": "string",
            "seller_city": "string",
            "seller_state": "string",
        },
    )

    operations = []

    for row in df.to_dict("records"):
        document = {
            "seller_id": clean_value(row["seller_id"]),
            "location": {
                "zip_code_prefix": clean_zip_code(
                    row["seller_zip_code_prefix"]
                ),
                "city": clean_value(row["seller_city"]),
                "state": clean_value(row["seller_state"]),
            },
        }

        operations.append(
            UpdateOne(
                {"seller_id": document["seller_id"]},
                {"$set": document},
                upsert=True,
            )
        )

    if operations:
        db.sellers.bulk_write(
            operations,
            ordered=False,
        )

    print(f"Sellers chargés : {len(operations)}")


# ============================================================
# GEOLOCATIONS
# ============================================================

def load_geolocations(db) -> None:
    """
    Charge les géolocalisations par lots.

    Le fichier Olist contient environ 1 million de lignes.
    Le paramètre chunksize évite de charger tout le fichier
    en mémoire.

    La clé logique d'une géolocalisation est :
    ZIP + latitude + longitude.
    """
    path = PROCESSED_DIR / "geolocation.csv"

    collection = db.geolocations

    total_rows = 0
    total_operations = 0

    print("Chargement des géolocalisations par lots...")

    for chunk_number, df in enumerate(
        pd.read_csv(
            path,
            dtype={
                "geolocation_zip_code_prefix": "string",
                "geolocation_lat": "float64",
                "geolocation_lng": "float64",
                "geolocation_city": "string",
                "geolocation_state": "string",
            },
            chunksize=BATCH_SIZE,
        ),
        start=1,
    ):
        operations = []

        for row in df.itertuples(index=False):
            zip_code = clean_zip_code(
                row.geolocation_zip_code_prefix
            )

            if (
                zip_code is None
                or pd.isna(row.geolocation_lat)
                or pd.isna(row.geolocation_lng)
            ):
                continue

            latitude = float(row.geolocation_lat)
            longitude = float(row.geolocation_lng)

            city = (
                str(row.geolocation_city).strip().lower()
                if pd.notna(row.geolocation_city)
                else ""
            )

            state = (
                str(row.geolocation_state).strip().upper()
                if pd.notna(row.geolocation_state)
                else ""
            )

            document = {
                "zip_code_prefix": zip_code,
                "location": {
                    "lat": latitude,
                    "lng": longitude,
                },
                "city": city,
                "state": state,
            }

            operations.append(
                UpdateOne(
                    {
                        "zip_code_prefix": zip_code,
                        "location.lat": latitude,
                        "location.lng": longitude,
                    },
                    {
                        "$set": document,
                    },
                    upsert=True,
                )
            )

        if operations:
            collection.bulk_write(
                operations,
                ordered=False,
            )

        total_rows += len(df)
        total_operations += len(operations)

        if chunk_number % 50 == 0:
            print(
                f"  {total_rows:,} lignes de géolocalisation "
                "traitées..."
            )

    print(
        "Géolocalisations chargées : "
        f"{total_operations:,} opérations."
    )


# ============================================================
# ORDER ITEMS
# ============================================================

def build_items() -> dict:
    """Regroupe les articles par commande."""
    path = PROCESSED_DIR / "order_items.csv"

    df = pd.read_csv(path)

    items_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(row["order_id"])

        item = {
            "order_item_id": clean_value(
                row["order_item_id"]
            ),
            "product_id": clean_value(row["product_id"]),
            "seller_id": clean_value(row["seller_id"]),
            "shipping_limit_date": parse_date(
                row["shipping_limit_date"]
            ),
            "price": clean_value(row["price"]),
            "freight_value": clean_value(
                row["freight_value"]
            ),
        }

        items_by_order.setdefault(
            order_id,
            [],
        ).append(item)

    return items_by_order


# ============================================================
# PAYMENTS
# ============================================================

def build_payments() -> dict:
    """Regroupe les paiements par commande."""
    path = PROCESSED_DIR / "payments.csv"

    df = pd.read_csv(path)

    payments_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(row["order_id"])

        payment = {
            "sequential": clean_value(
                row["payment_sequential"]
            ),
            "type": clean_value(
                row["payment_type"]
            ),
            "installments": clean_value(
                row["payment_installments"]
            ),
            "value": clean_value(
                row["payment_value"]
            ),
        }

        payments_by_order.setdefault(
            order_id,
            [],
        ).append(payment)

    return payments_by_order


# ============================================================
# REVIEWS
# ============================================================

def build_reviews() -> dict:
    """Regroupe les avis par commande."""
    path = PROCESSED_DIR / "reviews.csv"

    df = pd.read_csv(path)

    reviews_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(row["order_id"])

        review = {
            "review_id": clean_value(
                row["review_id"]
            ),
            "score": clean_value(
                row["review_score"]
            ),
            "comment_title": clean_value(
                row["review_comment_title"]
            ),
            "comment_message": clean_value(
                row["review_comment_message"]
            ),
            "created_at": parse_date(
                row["review_creation_date"]
            ),
            "answered_at": parse_date(
                row["review_answer_timestamp"]
            ),
        }

        reviews_by_order.setdefault(
            order_id,
            [],
        ).append(review)

    return reviews_by_order


# ============================================================
# ORDERS
# ============================================================

def load_orders(db) -> None:
    """Construit et charge les commandes dans MongoDB."""
    path = PROCESSED_DIR / "orders.csv"

    orders_df = pd.read_csv(path)

    items_by_order = build_items()
    payments_by_order = build_payments()
    reviews_by_order = build_reviews()

    operations = []

    date_mapping = {
        "purchase": "order_purchase_timestamp",
        "approved": "order_approved_at",
        "delivered_carrier": (
            "order_delivered_carrier_date"
        ),
        "delivered_customer": (
            "order_delivered_customer_date"
        ),
        "estimated_delivery": (
            "order_estimated_delivery_date"
        ),
    }

    for row in orders_df.to_dict("records"):
        order_id = clean_value(row["order_id"])

        dates = {}

        for target_name, source_name in date_mapping.items():
            value = parse_date(row[source_name])

            if value is not None:
                dates[target_name] = value

        document = {
            "order_id": order_id,
            "customer_id": clean_value(
                row["customer_id"]
            ),
            "status": clean_value(
                row["order_status"]
            ),
            "dates": dates,
            "items": items_by_order.get(
                order_id,
                [],
            ),
            "payments": payments_by_order.get(
                order_id,
                [],
            ),
            "reviews": reviews_by_order.get(
                order_id,
                [],
            ),
        }

        operations.append(
            UpdateOne(
                {"order_id": order_id},
                {"$set": document},
                upsert=True,
            )
        )

    if operations:
        db.orders.bulk_write(
            operations,
            ordered=False,
        )

    print(f"Orders chargées : {len(operations)}")


# ============================================================
# INDEX
# ============================================================

def create_indexes(db) -> None:
    """Crée les index nécessaires aux requêtes de l'API."""

    db.customers.create_index(
        "customer_id",
        unique=True,
    )

    db.customers.create_index(
        "customer_unique_id",
    )

    db.products.create_index(
        "product_id",
        unique=True,
    )

    db.sellers.create_index(
        "seller_id",
        unique=True,
    )

    db.orders.create_index(
        "order_id",
        unique=True,
    )

    db.orders.create_index(
        "customer_id",
    )

    db.orders.create_index(
        "status",
    )

    db.orders.create_index(
        "items.product_id",
    )

    db.orders.create_index(
        "items.seller_id",
    )

    db.geolocations.create_index(
        [
            ("zip_code_prefix", 1),
            ("location.lat", 1),
            ("location.lng", 1),
        ],
        unique=True,
    )

    print("Index MongoDB créés.")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Exécute le chargement complet du dataset Olist."""
    client = None

    try:
        client, db = get_database()

        print("\n" + "=" * 60)
        print("CHARGEMENT OLIST → MONGODB")
        print("=" * 60)

        load_customers(db)
        load_products(db)
        load_sellers(db)
        load_geolocations(db)
        load_orders(db)

        create_indexes(db)

        print("\nChargement MongoDB terminé.")

    except Exception as error:
        print(f"Erreur lors du chargement : {error}")
        raise

    finally:
        if client is not None:
            client.close()
            print("Connexion MongoDB fermée.")


if __name__ == "__main__":
    main()

