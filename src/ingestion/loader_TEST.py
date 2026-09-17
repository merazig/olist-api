import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = BASE_DIR / "data" / "processed"

LOAD_MODE = "TEST"
TEST_ORDER_LIMIT = 100
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
# UTILITAIRES
# ============================================================

def clean_string(value) -> str:
    """Convertit une valeur en chaîne propre."""
    if pd.isna(value):
        return ""

    return str(value).strip()


def clean_zip_code(value) -> str:
    """
    Conserve un code postal sur 5 caractères.

    Exemples :
        1000  -> 01000
        9756  -> 09756
        14409 -> 14409
    """
    if pd.isna(value):
        return ""

    value = str(value).strip()

    # Évite les valeurs du type 1000.0
    value = value.removesuffix(".0")

    return value.zfill(5)


def to_number(value):
    """Convertit une valeur en nombre."""
    if pd.isna(value):
        return None

    return float(value)


def to_integer(value):
    """Convertit une valeur en entier."""
    if pd.isna(value):
        return None

    return int(float(value))


def to_date(value):
    """Convertit une date pandas en chaîne ISO."""
    if pd.isna(value):
        return None

    return pd.Timestamp(value).isoformat()


def load_csv(filename: str, **kwargs) -> pd.DataFrame:
    """Charge un fichier CSV depuis data/processed."""
    path = PROCESSED_DIR / filename
    return pd.read_csv(path, **kwargs)


# ============================================================
# TRADUCTIONS
# ============================================================

def load_category_translations() -> dict:
    """Charge les traductions portugais -> anglais."""

    df = load_csv(
        "category_translation.csv",
        dtype="string",
    )

    translations = {}

    for _, row in df.iterrows():
        portuguese = clean_string(
            row["product_category_name"]
        ).lower()

        english = clean_string(
            row["product_category_name_english"]
        ).lower()

        translations[portuguese] = english

    print(
        f"Traductions de catégories : "
        f"{len(translations)}"
    )

    return translations


# ============================================================
# ORDERS
# ============================================================

def load_orders_scope() -> pd.DataFrame:
    """
    Charge les commandes.
    En TEST, limite le nombre de commandes.
    """

    df = load_csv(
        "orders.csv",
        dtype={
            "order_id": "string",
            "customer_id": "string",
        },
    )

    if LOAD_MODE == "TEST":
        df = df.head(TEST_ORDER_LIMIT).copy()

        print(
            f"MODE TEST : "
            f"{len(df)} commandes sélectionnées."
        )
    else:
        print(
            f"MODE FULL : "
            f"{len(df)} commandes sélectionnées."
        )

    return df


# ============================================================
# CUSTOMERS
# ============================================================

def load_customers(
    db,
    orders: pd.DataFrame,
) -> set[str]:
    """Charge les clients associés aux commandes."""

    customer_ids = set(
        orders["customer_id"]
        .dropna()
        .astype(str)
    )

    df = load_csv(
        "customers.csv",
        dtype={
            "customer_id": "string",
            "customer_unique_id": "string",
            "customer_zip_code_prefix": "string",
        },
    )

    df = df[
        df["customer_id"].isin(customer_ids)
    ].copy()

    operations = []

    for _, row in df.iterrows():

        document = {
            "customer_id": clean_string(
                row["customer_id"]
            ),
            "customer_unique_id": clean_string(
                row["customer_unique_id"]
            ),
            "location": {
                "zip_code_prefix": clean_zip_code(
                    row["customer_zip_code_prefix"]
                ),
                "city": clean_string(
                    row["customer_city"]
                ).lower(),
                "state": clean_string(
                    row["customer_state"]
                ).upper(),
            },
        }

        operations.append(
            UpdateOne(
                {
                    "customer_id":
                        document["customer_id"]
                },
                {
                    "$set": document
                },
                upsert=True,
            )
        )

    if operations:
        db.customers.bulk_write(
            operations,
            ordered=False,
        )

    print(
        f"Clients chargés : {len(df)}"
    )

    return customer_ids


# ============================================================
# PRODUCTS
# ============================================================

def load_products(
    db,
    orders: pd.DataFrame,
    translations: dict,
) -> set[str]:
    """Charge les produits présents dans les commandes."""

    items = load_csv(
        "order_items.csv",
        dtype={
            "order_id": "string",
            "product_id": "string",
        },
    )

    items = items[
        items["order_id"].isin(
            set(orders["order_id"])
        )
    ]

    product_ids = set(
        items["product_id"]
        .dropna()
        .astype(str)
    )

    df = load_csv(
        "products.csv",
        dtype={
            "product_id": "string",
        },
    )

    df = df[
        df["product_id"].isin(product_ids)
    ].copy()

    operations = []

    for _, row in df.iterrows():

        category_name = clean_string(
            row["product_category_name"]
        ).lower()

        document = {
            "product_id": clean_string(
                row["product_id"]
            ),
            "category": {
                "name": category_name,
                "name_en": translations.get(
                    category_name,
                    "unknown",
                ),
            },
            "attributes": {
                "name_length": to_integer(
                    row["product_name_lenght"]
                ),
                "description_length": to_integer(
                    row["product_description_lenght"]
                ),
                "photos_qty": to_integer(
                    row["product_photos_qty"]
                ),
            },
            "dimensions": {
                "weight_g": to_number(
                    row["product_weight_g"]
                ),
                "length_cm": to_number(
                    row["product_length_cm"]
                ),
                "height_cm": to_number(
                    row["product_height_cm"]
                ),
                "width_cm": to_number(
                    row["product_width_cm"]
                ),
            },
        }

        operations.append(
            UpdateOne(
                {
                    "product_id":
                        document["product_id"]
                },
                {
                    "$set": document
                },
                upsert=True,
            )
        )

    if operations:
        db.products.bulk_write(
            operations,
            ordered=False,
        )

    print(
        f"Produits chargés : {len(df)}"
    )

    return product_ids


# ============================================================
# SELLERS
# ============================================================

def load_sellers(
    db,
    orders: pd.DataFrame,
) -> set[str]:
    """Charge les vendeurs présents dans les commandes."""

    items = load_csv(
        "order_items.csv",
        dtype={
            "order_id": "string",
            "seller_id": "string",
        },
    )

    items = items[
        items["order_id"].isin(
            set(orders["order_id"])
        )
    ]

    seller_ids = set(
        items["seller_id"]
        .dropna()
        .astype(str)
    )

    df = load_csv(
        "sellers.csv",
        dtype={
            "seller_id": "string",
            "seller_zip_code_prefix": "string",
        },
    )

    df = df[
        df["seller_id"].isin(seller_ids)
    ].copy()

    operations = []

    for _, row in df.iterrows():

        document = {
            "seller_id": clean_string(
                row["seller_id"]
            ),
            "location": {
                "zip_code_prefix": clean_zip_code(
                    row["seller_zip_code_prefix"]
                ),
                "city": clean_string(
                    row["seller_city"]
                ).lower(),
                "state": clean_string(
                    row["seller_state"]
                ).upper(),
            },
        }

        operations.append(
            UpdateOne(
                {
                    "seller_id":
                        document["seller_id"]
                },
                {
                    "$set": document
                },
                upsert=True,
            )
        )

    if operations:
        db.sellers.bulk_write(
            operations,
            ordered=False,
        )

    print(
        f"Vendeurs chargés : {len(df)}"
    )

    return seller_ids


# ============================================================
# ORDER ITEMS
# ============================================================

def build_order_items(
    orders: pd.DataFrame,
) -> dict:
    """Prépare les articles par commande."""

    df = load_csv(
        "order_items.csv",
        dtype={
            "order_id": "string",
            "product_id": "string",
            "seller_id": "string",
        },
    )

    df = df[
        df["order_id"].isin(
            set(orders["order_id"])
        )
    ].copy()

    grouped = {}

    for order_id, group in df.groupby(
        "order_id"
    ):
        grouped[order_id] = []

        for _, row in group.iterrows():

            item = {
                "order_item_id": to_integer(
                    row["order_item_id"]
                ),
                "product_id": clean_string(
                    row["product_id"]
                ),
                "seller_id": clean_string(
                    row["seller_id"]
                ),
                "shipping_limit_date": to_date(
                    row["shipping_limit_date"]
                ),
                "price": to_number(
                    row["price"]
                ),
                "freight_value": to_number(
                    row["freight_value"]
                ),
            }

            grouped[order_id].append(item)

    print(
        f"Articles associés : {len(df)}"
    )

    return grouped


# ============================================================
# PAYMENTS
# ============================================================

def build_payments(
    orders: pd.DataFrame,
) -> dict:
    """Prépare les paiements par commande."""

    df = load_csv(
        "payments.csv",
        dtype={
            "order_id": "string",
            "payment_type": "string",
        },
    )

    df = df[
        df["order_id"].isin(
            set(orders["order_id"])
        )
    ].copy()

    grouped = {}

    for order_id, group in df.groupby(
        "order_id"
    ):
        grouped[order_id] = []

        for _, row in group.iterrows():

            payment = {
                "sequential": to_integer(
                    row["payment_sequential"]
                ),
                "type": clean_string(
                    row["payment_type"]
                ),
                "installments": to_integer(
                    row["payment_installments"]
                ),
                "value": to_number(
                    row["payment_value"]
                ),
            }

            grouped[order_id].append(payment)

    print(
        f"Paiements associés : {len(df)}"
    )

    return grouped


# ============================================================
# REVIEWS
# ============================================================

def build_reviews(
    orders: pd.DataFrame,
) -> dict:
    """Prépare les avis par commande."""

    df = load_csv(
        "reviews.csv",
        dtype={
            "review_id": "string",
            "order_id": "string",
        },
    )

    df = df[
        df["order_id"].isin(
            set(orders["order_id"])
        )
    ].copy()

    grouped = {}

    for order_id, group in df.groupby(
        "order_id"
    ):
        grouped[order_id] = []

        for _, row in group.iterrows():

            review = {
                "review_id": clean_string(
                    row["review_id"]
                ),
                "score": to_integer(
                    row["review_score"]
                ),
                "comment_title": clean_string(
                    row["review_comment_title"]
                ),
                "comment_message": clean_string(
                    row["review_comment_message"]
                ),
                "created_at": to_date(
                    row["review_creation_date"]
                ),
                "answered_at": to_date(
                    row["review_answer_timestamp"]
                ),
            }

            grouped[order_id].append(review)

    print(
        f"Avis associés : {len(df)}"
    )

    return grouped


# ============================================================
# ORDERS → MONGODB
# ============================================================

def load_orders(
    db,
    orders: pd.DataFrame,
) -> None:
    """Crée les commandes MongoDB avec données embarquées."""

    items = build_order_items(orders)
    payments = build_payments(orders)
    reviews = build_reviews(orders)

    operations = []

    for _, row in orders.iterrows():

        order_id = clean_string(
            row["order_id"]
        )

        document = {
            "order_id": order_id,
            "customer_id": clean_string(
                row["customer_id"]
            ),
            "status": clean_string(
                row["order_status"]
            ),
            "dates": {
                "purchase": to_date(
                    row["order_purchase_timestamp"]
                ),
                "approved": to_date(
                    row["order_approved_at"]
                ),
                "delivered_carrier": to_date(
                    row["order_delivered_carrier_date"]
                ),
                "delivered_customer": to_date(
                    row["order_delivered_customer_date"]
                ),
                "estimated_delivery": to_date(
                    row["order_estimated_delivery_date"]
                ),
            },
            "items": items.get(
                order_id,
                [],
            ),
            "payments": payments.get(
                order_id,
                [],
            ),
            "reviews": reviews.get(
                order_id,
                [],
            ),
        }

        operations.append(
            UpdateOne(
                {
                    "order_id": order_id
                },
                {
                    "$set": document
                },
                upsert=True,
            )
        )

    if operations:
        db.orders.bulk_write(
            operations,
            ordered=False,
        )

    print(
        f"Commandes chargées : "
        f"{len(orders)}"
    )


# ============================================================
# GEOLOCALISATIONS
# ============================================================

def load_geolocations(
    db,
    customer_ids: set[str],
    seller_ids: set[str],
) -> None:
    """
    Charge les géolocalisations.

    En TEST :
        uniquement les ZIP utilisés par les clients
        et vendeurs sélectionnés.

    En FULL :
        toutes les géolocalisations.
    """

    customers = load_csv(
        "customers.csv",
        dtype={
            "customer_id": "string",
            "customer_zip_code_prefix": "string",
        },
    )

    sellers = load_csv(
        "sellers.csv",
        dtype={
            "seller_id": "string",
            "seller_zip_code_prefix": "string",
        },
    )

    customer_zips = set(
        customers[
            customers["customer_id"].isin(
                customer_ids
            )
        ]["customer_zip_code_prefix"]
        .dropna()
        .map(clean_zip_code)
    )

    seller_zips = set(
        sellers[
            sellers["seller_id"].isin(
                seller_ids
            )
        ]["seller_zip_code_prefix"]
        .dropna()
        .map(clean_zip_code)
    )

    relevant_zips = customer_zips | seller_zips

    df = load_csv(
        "geolocation.csv",
        dtype={
            "geolocation_zip_code_prefix":
                "string",
        },
    )

    df["geolocation_zip_code_prefix"] = (
        df["geolocation_zip_code_prefix"]
        .map(clean_zip_code)
    )

    if LOAD_MODE == "TEST":
        df = df[
            df["geolocation_zip_code_prefix"]
            .isin(relevant_zips)
        ].copy()

    operations = []

    for _, row in df.iterrows():

        zip_code = clean_zip_code(
            row["geolocation_zip_code_prefix"]
        )

        lat = to_number(
            row["geolocation_lat"]
        )

        lng = to_number(
            row["geolocation_lng"]
        )

        document = {
            "zip_code_prefix": zip_code,
            "location": {
                "lat": lat,
                "lng": lng,
            },
            "city": clean_string(
                row["geolocation_city"]
            ).lower(),
            "state": clean_string(
                row["geolocation_state"]
            ).upper(),
        }

        operations.append(
            UpdateOne(
                {
                    "zip_code_prefix": zip_code,
                    "location.lat": lat,
                    "location.lng": lng,
                },
                {
                    "$set": document
                },
                upsert=True,
            )
        )

        if len(operations) >= BATCH_SIZE:
            db.geolocations.bulk_write(
                operations,
                ordered=False,
            )
            operations = []

    if operations:
        db.geolocations.bulk_write(
            operations,
            ordered=False,
        )

    print(
        f"Géolocalisations chargées : "
        f"{len(df)}"
    )


# ============================================================
# INDEX
# ============================================================

def create_indexes(db) -> None:
    """Crée les index MongoDB."""

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

    db.products.create_index(
        "category.name",
    )

    db.products.create_index(
        "category.name_en",
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
        "dates.purchase",
    )

    db.geolocations.create_index(
        "zip_code_prefix",
    )

    db.geolocations.create_index(
        [
            ("location.lat", 1),
            ("location.lng", 1),
        ],
    )

    print("Index MongoDB créés.")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Charge les données Olist dans MongoDB."""

    print("=" * 60)
    print("CHARGEMENT OLIST → MONGODB")
    print("=" * 60)

    print(f"Mode : {LOAD_MODE}")

    if LOAD_MODE == "TEST":
        print(
            f"Limite TEST : "
            f"{TEST_ORDER_LIMIT} commandes"
        )

    client = MongoClient(MONGO_URI)

    try:
        client.admin.command("ping")

        print(
            f"Connexion MongoDB OK : "
            f"{MONGO_DATABASE}"
        )

        db = client[MONGO_DATABASE]

        translations = load_category_translations()

        orders = load_orders_scope()

        customer_ids = load_customers(
            db,
            orders,
        )

        product_ids = load_products(
            db,
            orders,
            translations,
        )

        seller_ids = load_sellers(
            db,
            orders,
        )

        load_geolocations(
            db,
            customer_ids,
            seller_ids,
        )

        load_orders(
            db,
            orders,
        )

        create_indexes(db)

        print()
        print("=" * 60)
        print("RÉSUMÉ MONGODB")
        print("=" * 60)

        print(
            f"customers      : "
            f"{db.customers.count_documents({})}"
        )

        print(
            f"products       : "
            f"{db.products.count_documents({})}"
        )

        print(
            f"sellers        : "
            f"{db.sellers.count_documents({})}"
        )

        print(
            f"orders         : "
            f"{db.orders.count_documents({})}"
        )

        print(
            f"geolocations   : "
            f"{db.geolocations.count_documents({})}"
        )

        print()
        print("=" * 60)
        print("CHARGEMENT TERMINÉ")
        print("=" * 60)

    finally:
        client.close()
        print("Connexion MongoDB fermée.")


if __name__ == "__main__":
    main()