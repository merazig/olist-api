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
GEO_BATCH_SIZE = 500

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
    """Establish and verify the MongoDB connection."""
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=120000,
        retryWrites=True,
    )

    client.admin.command("ping")

    print("Connexion MongoDB réussie.")

    return client, client[MONGO_DATABASE]


# ============================================================
# UTILITAIRES
# ============================================================

def parse_date(value):
    """Convert a value to a Python datetime or return None."""
    if pd.isna(value):
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.to_pydatetime()


def clean_value(value):
    """Convert pandas missing values to None."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def clean_zip_code(value) -> str | None:
    """Normalize a ZIP code to five characters."""
    if pd.isna(value):
        return None

    value = str(value).strip()
    value = value.removesuffix(".0")

    return value.zfill(5)


def execute_bulk_operations(
    collection,
    operations,
    batch_size=BATCH_SIZE,
):
    """Execute MongoDB bulk operations in small batches."""
    total = 0

    for start in range(0, len(operations), batch_size):
        batch = operations[start:start + batch_size]

        if not batch:
            continue

        collection.bulk_write(
            batch,
            ordered=False,
        )

        total += len(batch)

    return total


def get_existing_ids(
    collection,
    field,
    ids,
    batch_size=BATCH_SIZE,
):
    """Return IDs already present in a MongoDB collection."""
    existing = set()

    ids = [
        value
        for value in ids
        if value is not None
    ]

    for start in range(0, len(ids), batch_size):
        batch = ids[start:start + batch_size]

        if not batch:
            continue

        cursor = collection.find(
            {field: {"$in": batch}},
            {"_id": 0, field: 1},
        )

        for document in cursor:
            value = document.get(field)

            if value is not None:
                existing.add(value)

    return existing


# ============================================================
# INDEX
# ============================================================

def create_indexes(db) -> None:
    """Create indexes required during and after ingestion."""

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
# CUSTOMERS
# ============================================================

def load_customers(db) -> None:
    """Insert only customers that do not already exist."""
    path = PROCESSED_DIR / "customers.csv"
    collection = db.customers

    total_read = 0
    total_inserted = 0
    total_existing = 0

    print("\n--- CUSTOMERS ---")

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
        documents = []

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

            documents.append(document)

        ids = [
            document["customer_id"]
            for document in documents
        ]

        existing_ids = get_existing_ids(
            collection,
            "customer_id",
            ids,
        )

        new_documents = [
            document
            for document in documents
            if document["customer_id"] not in existing_ids
        ]

        if new_documents:
            collection.insert_many(
                new_documents,
                ordered=False,
            )

        total_read += len(documents)
        total_inserted += len(new_documents)
        total_existing += len(existing_ids)

        print(
            f"  Lues : {total_read:,} | "
            f"Nouvelles : {total_inserted:,} | "
            f"Déjà présentes : {total_existing:,}"
        )

    print(
        f"Clients terminés : "
        f"{total_inserted:,} nouveaux / "
        f"{total_existing:,} déjà présents."
    )


# ============================================================
# PRODUCTS
# ============================================================

def load_products(db) -> None:
    """Insert only products that do not already exist."""
    products_path = PROCESSED_DIR / "products.csv"
    translation_path = (
        PROCESSED_DIR / "category_translation.csv"
    )

    collection = db.products

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

    total_read = 0
    total_inserted = 0
    total_existing = 0

    print("\n--- PRODUCTS ---")

    for chunk in pd.read_csv(
        products_path,
        chunksize=BATCH_SIZE,
    ):
        documents = []

        for row in chunk.to_dict("records"):
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

            documents.append(document)

        ids = [
            document["product_id"]
            for document in documents
        ]

        existing_ids = get_existing_ids(
            collection,
            "product_id",
            ids,
        )

        new_documents = [
            document
            for document in documents
            if document["product_id"] not in existing_ids
        ]

        if new_documents:
            collection.insert_many(
                new_documents,
                ordered=False,
            )

        total_read += len(documents)
        total_inserted += len(new_documents)
        total_existing += len(existing_ids)

        print(
            f"  Lues : {total_read:,} | "
            f"Nouveaux : {total_inserted:,} | "
            f"Déjà présents : {total_existing:,}"
        )

    print(
        f"Produits terminés : "
        f"{total_inserted:,} nouveaux / "
        f"{total_existing:,} déjà présents."
    )

    print(
        f"Traductions de catégories : "
        f"{len(translations):,}"
    )


# ============================================================
# SELLERS
# ============================================================

def load_sellers(db) -> None:
    """Insert only sellers that do not already exist."""
    path = PROCESSED_DIR / "sellers.csv"
    collection = db.sellers

    total_read = 0
    total_inserted = 0
    total_existing = 0

    print("\n--- SELLERS ---")

    for chunk in pd.read_csv(
        path,
        dtype={
            "seller_id": "string",
            "seller_zip_code_prefix": "string",
            "seller_city": "string",
            "seller_state": "string",
        },
        chunksize=BATCH_SIZE,
    ):
        documents = []

        for row in chunk.to_dict("records"):
            document = {
                "seller_id": clean_value(
                    row["seller_id"]
                ),
                "location": {
                    "zip_code_prefix": clean_zip_code(
                        row["seller_zip_code_prefix"]
                    ),
                    "city": (
                        str(row["seller_city"])
                        .strip()
                        .lower()
                        if pd.notna(row["seller_city"])
                        else ""
                    ),
                    "state": (
                        str(row["seller_state"])
                        .strip()
                        .upper()
                        if pd.notna(row["seller_state"])
                        else ""
                    ),
                },
            }

            documents.append(document)

        ids = [
            document["seller_id"]
            for document in documents
        ]

        existing_ids = get_existing_ids(
            collection,
            "seller_id",
            ids,
        )

        new_documents = [
            document
            for document in documents
            if document["seller_id"] not in existing_ids
        ]

        if new_documents:
            collection.insert_many(
                new_documents,
                ordered=False,
            )

        total_read += len(documents)
        total_inserted += len(new_documents)
        total_existing += len(existing_ids)

        print(
            f"  Lus : {total_read:,} | "
            f"Nouveaux : {total_inserted:,} | "
            f"Déjà présents : {total_existing:,}"
        )

    print(
        f"Vendeurs terminés : "
        f"{total_inserted:,} nouveaux / "
        f"{total_existing:,} déjà présents."
    )


# ============================================================
# GEOLOCATIONS
# ============================================================

def load_geolocations(db) -> None:
    """
    Insert only new geolocation points.

    Logical key:
    ZIP + latitude + longitude.
    """
    path = PROCESSED_DIR / "geolocation.csv"
    collection = db.geolocations

    total_read = 0
    total_inserted = 0
    total_existing = 0

    print("\n--- GEOLOCATIONS ---")
    print(
        "Reprise des géolocalisations "
        "sans réinsérer les points existants..."
    )

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
        df = df.dropna(
            subset=[
                "geolocation_zip_code_prefix",
                "geolocation_lat",
                "geolocation_lng",
            ]
        ).copy()

        df["zip_code_prefix"] = (
            df["geolocation_zip_code_prefix"]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\.0$",
                "",
                regex=True,
            )
            .str.zfill(5)
        )

        df = df.drop_duplicates(
            subset=[
                "zip_code_prefix",
                "geolocation_lat",
                "geolocation_lng",
            ]
        )

        documents = []

        for row in df.itertuples(index=False):
            zip_code = clean_zip_code(
                row.zip_code_prefix
            )

            latitude = float(
                row.geolocation_lat
            )

            longitude = float(
                row.geolocation_lng
            )

            city = (
                str(row.geolocation_city)
                .strip()
                .lower()
                if pd.notna(row.geolocation_city)
                else ""
            )

            state = (
                str(row.geolocation_state)
                .strip()
                .upper()
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

            documents.append(document)

        # Recherche des clés déjà présentes.
        existing_keys = set()

        for start in range(
            0,
            len(documents),
            GEO_BATCH_SIZE,
        ):
            batch = documents[
                start:start + GEO_BATCH_SIZE
            ]

            conditions = [
                {
                    "zip_code_prefix": document[
                        "zip_code_prefix"
                    ],
                    "location.lat": document[
                        "location"
                    ]["lat"],
                    "location.lng": document[
                        "location"
                    ]["lng"],
                }
                for document in batch
            ]

            if not conditions:
                continue

            cursor = collection.find(
                {"$or": conditions},
                {
                    "_id": 0,
                    "zip_code_prefix": 1,
                    "location.lat": 1,
                    "location.lng": 1,
                },
            )

            for document in cursor:
                key = (
                    document["zip_code_prefix"],
                    document["location"]["lat"],
                    document["location"]["lng"],
                )

                existing_keys.add(key)

        new_documents = []

        for document in documents:
            key = (
                document["zip_code_prefix"],
                document["location"]["lat"],
                document["location"]["lng"],
            )

            if key not in existing_keys:
                new_documents.append(document)

        if new_documents:
            collection.insert_many(
                new_documents,
                ordered=False,
            )

        total_read += len(documents)
        total_inserted += len(new_documents)
        total_existing += len(existing_keys)

        if chunk_number % 10 == 0:
            print(
                f"  Lues : {total_read:,} | "
                f"Nouvelles : {total_inserted:,} | "
                f"Déjà présentes : {total_existing:,}"
            )

    print(
        "Géolocalisations terminées : "
        f"{total_inserted:,} nouvelles / "
        f"{total_existing:,} déjà présentes."
    )


# ============================================================
# ORDER ITEMS
# ============================================================

def build_items() -> dict:
    """Group order items by order ID."""
    path = PROCESSED_DIR / "order_items.csv"

    df = pd.read_csv(path)

    items_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(
            row["order_id"]
        )

        item = {
            "order_item_id": clean_value(
                row["order_item_id"]
            ),
            "product_id": clean_value(
                row["product_id"]
            ),
            "seller_id": clean_value(
                row["seller_id"]
            ),
            "shipping_limit_date": parse_date(
                row["shipping_limit_date"]
            ),
            "price": clean_value(
                row["price"]
            ),
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
    """Group payments by order ID."""
    path = PROCESSED_DIR / "payments.csv"

    df = pd.read_csv(path)

    payments_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(
            row["order_id"]
        )

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
    """Group reviews by order ID."""
    path = PROCESSED_DIR / "reviews.csv"

    df = pd.read_csv(path)

    reviews_by_order = {}

    for row in df.to_dict("records"):
        order_id = clean_value(
            row["order_id"]
        )

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
    """Load orders with embedded items, payments and reviews."""
    path = PROCESSED_DIR / "orders.csv"
    collection = db.orders

    print("\n--- ORDERS ---")

    print("Préparation des articles...")
    items_by_order = build_items()

    print("Préparation des paiements...")
    payments_by_order = build_payments()

    print("Préparation des avis...")
    reviews_by_order = build_reviews()

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

    total = 0

    for chunk in pd.read_csv(
        path,
        chunksize=BATCH_SIZE,
    ):
        operations = []

        for row in chunk.to_dict("records"):
            order_id = clean_value(
                row["order_id"]
            )

            dates = {}

            for target_name, source_name in date_mapping.items():
                value = parse_date(
                    row[source_name]
                )

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

        execute_bulk_operations(
            collection,
            operations,
        )

        total += len(operations)

        print(
            f"  Commandes chargées : "
            f"{total:,}"
        )

    print(
        f"Commandes terminées : {total:,}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Run the complete Olist loading process."""
    client = None

    try:
        client, db = get_database()

        print("\n" + "=" * 60)
        print("CHARGEMENT OLIST → MONGODB")
        print("=" * 60)

        # Les index sont créés AVANT les recherches
        # de documents existants.
        create_indexes(db)

        load_customers(db)
        load_products(db)
        load_sellers(db)
        load_geolocations(db)
        load_orders(db)

        print("\nChargement MongoDB terminé.")

    except Exception as error:
        print(
            f"Erreur lors du chargement : {error}"
        )
        raise

    finally:
        if client is not None:
            client.close()
            print(
                "Connexion MongoDB fermée."
            )


if __name__ == "__main__":
    main()