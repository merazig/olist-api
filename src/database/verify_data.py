import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017",
)

MONGO_DATABASE = os.getenv(
    "MONGO_DATABASE",
    "olist",
)

BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

# ------------------------------------------------------------
# Mode de vérification
# ------------------------------------------------------------

LOAD_MODE = "TEST"

TEST_ORDER_LIMIT = 100


# ============================================================
# OUTILS
# ============================================================

def normalize_text(value):
    """Normalise une valeur texte."""

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    return value if value else None


def normalize_zip(value):
    """
    Normalise un code postal.

    Un code postal est un identifiant et non une valeur numérique.
    Il est donc conservé comme chaîne de 5 caractères afin de
    préserver les zéros initiaux.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    # Supprime éventuellement le suffixe .0 créé par certains CSV.
    if value.endswith(".0"):
        value = value[:-2]

    return value.zfill(5)


def get_database():
    """Connexion à MongoDB."""

    client = MongoClient(MONGO_URI)

    client.admin.command("ping")

    db = client[MONGO_DATABASE]

    return client, db


# ============================================================
# CHARGEMENT DES DONNÉES ATTENDUES
# ============================================================

def load_expected_data():
    """
    Charge les CSV nettoyés et reconstruit exactement
    le périmètre attendu par le mode TEST ou FULL.
    """

    orders = pd.read_csv(
        PROCESSED_DIR / "orders.csv"
    )

    customers = pd.read_csv(
        PROCESSED_DIR / "customers.csv",
        dtype={
            "customer_zip_code_prefix": "string",
        },
    )

    products = pd.read_csv(
        PROCESSED_DIR / "products.csv"
    )

    sellers = pd.read_csv(
        PROCESSED_DIR / "sellers.csv",
        dtype={
            "seller_zip_code_prefix": "string",
        },
    )

    items = pd.read_csv(
        PROCESSED_DIR / "order_items.csv"
    )

    payments = pd.read_csv(
        PROCESSED_DIR / "payments.csv"
    )

    reviews = pd.read_csv(
        PROCESSED_DIR / "reviews.csv"
    )

    geolocations = pd.read_csv(
        PROCESSED_DIR / "geolocation.csv",
        dtype={
            "geolocation_zip_code_prefix": "string",
        },
    )

    translations = pd.read_csv(
        PROCESSED_DIR / "category_translation.csv"
    )

    # ========================================================
    # MODE TEST
    # ========================================================

    if LOAD_MODE == "TEST":

        # ----------------------------------------------------
        # 100 premières commandes
        # ----------------------------------------------------

        selected_orders = (
            orders
            .head(TEST_ORDER_LIMIT)
            .copy()
        )

        # IMPORTANT :
        # orders doit lui-même être limité.
        orders = selected_orders.copy()

        order_ids = set(
            selected_orders["order_id"]
        )

        # ----------------------------------------------------
        # Articles
        # ----------------------------------------------------

        items = items[
            items["order_id"].isin(order_ids)
        ].copy()

        # ----------------------------------------------------
        # Paiements
        # ----------------------------------------------------

        payments = payments[
            payments["order_id"].isin(order_ids)
        ].copy()

        # ----------------------------------------------------
        # Avis
        # ----------------------------------------------------

        reviews = reviews[
            reviews["order_id"].isin(order_ids)
        ].copy()

        # ----------------------------------------------------
        # Clients
        # ----------------------------------------------------

        customer_ids = set(
            selected_orders["customer_id"]
        )

        customers = customers[
            customers["customer_id"].isin(
                customer_ids
            )
        ].copy()

        # ----------------------------------------------------
        # Produits
        # ----------------------------------------------------

        product_ids = set(
            items["product_id"]
        )

        products = products[
            products["product_id"].isin(
                product_ids
            )
        ].copy()

        # ----------------------------------------------------
        # Vendeurs
        # ----------------------------------------------------

        seller_ids = set(
            items["seller_id"]
        )

        sellers = sellers[
            sellers["seller_id"].isin(
                seller_ids
            )
        ].copy()

        # ----------------------------------------------------
        # Géolocalisations
        # ----------------------------------------------------

        customer_zips = set(
            customers[
                "customer_zip_code_prefix"
            ]
            .dropna()
            .apply(normalize_zip)
        )

        seller_zips = set(
            sellers[
                "seller_zip_code_prefix"
            ]
            .dropna()
            .apply(normalize_zip)
        )

        geolocation_zips = (
            customer_zips
            | seller_zips
        )

        geolocations["geolocation_zip_code_prefix"] = (
            geolocations[
                "geolocation_zip_code_prefix"
            ]
            .apply(normalize_zip)
        )

        geolocations = geolocations[
            geolocations[
                "geolocation_zip_code_prefix"
            ].isin(
                geolocation_zips
            )
        ].copy()

    return {
        "orders": orders,
        "customers": customers,
        "products": products,
        "sellers": sellers,
        "items": items,
        "payments": payments,
        "reviews": reviews,
        "geolocations": geolocations,
        "translations": translations,
    }


# ============================================================
# 1. VOLUMES DES COLLECTIONS
# ============================================================

def check_collection_counts(db, expected):

    print("\n" + "=" * 60)
    print("1. VOLUMES DES COLLECTIONS")
    print("=" * 60)

    checks = [
        ("Commandes", "orders"),
        ("Clients", "customers"),
        ("Produits", "products"),
        ("Vendeurs", "sellers"),
    ]

    result = True

    for label, collection_name in checks:

        expected_count = len(
            expected[collection_name]
        )

        actual_count = (
            db[collection_name]
            .count_documents({})
        )

        ok = (
            actual_count
            == expected_count
        )

        print(
            f"{label:<25}"
            f"{actual_count:>5} / "
            f"{expected_count:<5}"
            f" [{'OK' if ok else 'ERREUR'}]"
        )

        result = result and ok

    return result


# ============================================================
# 2. DONNÉES EMBARQUÉES
# ============================================================

def check_embedded_data(db, expected):

    print("\n" + "=" * 60)
    print(
        "2. DONNÉES EMBARQUÉES "
        "DANS LES COMMANDES"
    )
    print("=" * 60)

    expected_items = len(
        expected["items"]
    )

    expected_payments = len(
        expected["payments"]
    )

    expected_reviews = len(
        expected["reviews"]
    )

    # --------------------------------------------------------
    # Articles
    # --------------------------------------------------------

    items_result = list(
        db.orders.aggregate(
            [
                {
                    "$project": {
                        "count": {
                            "$size": {
                                "$ifNull": [
                                    "$items",
                                    [],
                                ]
                            }
                        }
                    }
                }
            ]
        )
    )

    actual_items = sum(
        document["count"]
        for document in items_result
    )

    # --------------------------------------------------------
    # Paiements
    # --------------------------------------------------------

    payments_result = list(
        db.orders.aggregate(
            [
                {
                    "$project": {
                        "count": {
                            "$size": {
                                "$ifNull": [
                                    "$payments",
                                    [],
                                ]
                            }
                        }
                    }
                }
            ]
        )
    )

    actual_payments = sum(
        document["count"]
        for document in payments_result
    )

    # --------------------------------------------------------
    # Avis
    # --------------------------------------------------------

    reviews_result = list(
        db.orders.aggregate(
            [
                {
                    "$project": {
                        "count": {
                            "$size": {
                                "$ifNull": [
                                    "$reviews",
                                    [],
                                ]
                            }
                        }
                    }
                }
            ]
        )
    )

    actual_reviews = sum(
        document["count"]
        for document in reviews_result
    )

    checks = [
        (
            "Articles",
            actual_items,
            expected_items,
        ),
        (
            "Paiements",
            actual_payments,
            expected_payments,
        ),
        (
            "Avis",
            actual_reviews,
            expected_reviews,
        ),
    ]

    result = True

    for label, actual, expected_count in checks:

        ok = (
            actual
            == expected_count
        )

        print(
            f"{label:<25}"
            f"{actual:>5} / "
            f"{expected_count:<5}"
            f" [{'OK' if ok else 'ERREUR'}]"
        )

        result = result and ok

    return result


# ============================================================
# 3. IDENTIFIANTS
# ============================================================

def check_ids(db, expected):

    print("\n" + "=" * 60)
    print("3. VÉRIFICATION DES IDENTIFIANTS")
    print("=" * 60)

    checks = [
        (
            "Commandes",
            "orders",
            "order_id",
        ),
        (
            "Clients",
            "customers",
            "customer_id",
        ),
        (
            "Produits",
            "products",
            "product_id",
        ),
        (
            "Vendeurs",
            "sellers",
            "seller_id",
        ),
    ]

    result = True

    for label, collection_name, field in checks:

        expected_ids = set(
            expected[
                collection_name
            ][field]
        )

        actual_ids = set(
            db[collection_name]
            .distinct(field)
        )

        ok = (
            expected_ids
            == actual_ids
        )

        print(
            f"{label:<12}: "
            f"{'OK' if ok else 'ERREUR'}"
        )

        if not ok:

            missing = (
                expected_ids
                - actual_ids
            )

            extra = (
                actual_ids
                - expected_ids
            )

            if missing:
                print(
                    f"  IDs manquants : "
                    f"{len(missing)}"
                )

            if extra:
                print(
                    f"  IDs supplémentaires : "
                    f"{len(extra)}"
                )

        result = result and ok

    return result


# ============================================================
# 4. RÉFÉRENCES
# ============================================================

def check_references(db):

    print("\n" + "=" * 60)
    print("4. VÉRIFICATION DES RÉFÉRENCES")
    print("=" * 60)

    result = True

    # --------------------------------------------------------
    # Clients
    # --------------------------------------------------------

    customer_ids = set(
        db.customers.distinct(
            "customer_id"
        )
    )

    order_customer_ids = set(
        db.orders.distinct(
            "customer_id"
        )
    )

    orphan_customers = (
        order_customer_ids
        - customer_ids
    )

    ok_customers = (
        not orphan_customers
    )

    print(
        "Références clients  : "
        f"{'OK' if ok_customers else 'ERREUR'}"
    )

    result = (
        result
        and ok_customers
    )

    # --------------------------------------------------------
    # Produits
    # --------------------------------------------------------

    product_ids = set(
        db.products.distinct(
            "product_id"
        )
    )

    order_product_ids = set()

    cursor = db.orders.find(
        {},
        {
            "items.product_id": 1
        },
    )

    for order in cursor:

        for item in order.get(
            "items",
            [],
        ):

            product_id = item.get(
                "product_id"
            )

            if product_id:
                order_product_ids.add(
                    product_id
                )

    orphan_products = (
        order_product_ids
        - product_ids
    )

    ok_products = (
        not orphan_products
    )

    print(
        "Références produits : "
        f"{'OK' if ok_products else 'ERREUR'}"
    )

    result = (
        result
        and ok_products
    )

    # --------------------------------------------------------
    # Vendeurs
    # --------------------------------------------------------

    seller_ids = set(
        db.sellers.distinct(
            "seller_id"
        )
    )

    order_seller_ids = set()

    cursor = db.orders.find(
        {},
        {
            "items.seller_id": 1
        },
    )

    for order in cursor:

        for item in order.get(
            "items",
            [],
        ):

            seller_id = item.get(
                "seller_id"
            )

            if seller_id:
                order_seller_ids.add(
                    seller_id
                )

    orphan_sellers = (
        order_seller_ids
        - seller_ids
    )

    ok_sellers = (
        not orphan_sellers
    )

    print(
        "Références vendeurs : "
        f"{'OK' if ok_sellers else 'ERREUR'}"
    )

    result = (
        result
        and ok_sellers
    )

    return result


# ============================================================
# 5. INDEX MONGODB
# ============================================================

def check_indexes(db):

    print("\n" + "=" * 60)
    print("5. INDEX MONGODB")
    print("=" * 60)

    expected_indexes = {
        "customers": [
            "customer_id",
            "customer_unique_id",
        ],
        "products": [
            "product_id",
            "category.name",
            "category.name_en",
        ],
        "sellers": [
            "seller_id",
        ],
        "orders": [
            "order_id",
            "customer_id",
            "status",
            "dates.purchase",
        ],
        "geolocations": [
            "zip_code_prefix",
        ],
    }

    result = True

    for collection_name, fields in (
        expected_indexes.items()
    ):

        indexes = (
            db[collection_name]
            .list_indexes()
        )

        index_fields = set()

        for index in indexes:

            for field in index["key"]:

                index_fields.add(field)

        for field in fields:

            ok = (
                field
                in index_fields
            )

            print(
                f"{collection_name:<12}"
                f"{field:<25}"
                f"[{'OK' if ok else 'MANQUANT'}]"
            )

            result = (
                result
                and ok
            )

    return result


# ============================================================
# 6. GÉOLOCALISATIONS
# ============================================================

def check_geolocations(db, expected):

    print("\n" + "=" * 60)
    print("6. GÉOLOCALISATIONS")
    print("=" * 60)

    expected_geo = (
        expected["geolocations"]
    )

    # --------------------------------------------------------
    # Clés attendues
    # --------------------------------------------------------

    expected_keys = set()

    for _, row in expected_geo.iterrows():

        zip_code = normalize_zip(
            row[
                "geolocation_zip_code_prefix"
            ]
        )

        lat = float(
            row["geolocation_lat"]
        )

        lng = float(
            row["geolocation_lng"]
        )

        expected_keys.add(
            (
                zip_code,
                lat,
                lng,
            )
        )

    # --------------------------------------------------------
    # Clés MongoDB
    # --------------------------------------------------------

    actual_keys = set()

    cursor = db.geolocations.find(
        {},
        {
            "zip_code_prefix": 1,
            "location.lat": 1,
            "location.lng": 1,
        },
    )

    for document in cursor:

        location = document.get(
            "location",
            {},
        )

        zip_code = document.get(
            "zip_code_prefix"
        )

        lat = location.get("lat")

        lng = location.get("lng")

        if (
            zip_code is not None
            and lat is not None
            and lng is not None
        ):

            actual_keys.add(
                (
                    normalize_zip(zip_code),
                    float(lat),
                    float(lng),
                )
            )

    # --------------------------------------------------------
    # Comparaison
    # --------------------------------------------------------

    expected_count = len(
        expected_keys
    )

    actual_count = len(
        actual_keys
    )

    count_ok = (
        actual_count
        == expected_count
    )

    print(
        f"Géolocalisations        "
        f"{actual_count} / "
        f"{expected_count}"
        f" [{'OK' if count_ok else 'ERREUR'}]"
    )

    missing = (
        expected_keys
        - actual_keys
    )

    extra = (
        actual_keys
        - expected_keys
    )

    keys_ok = (
        not missing
        and not extra
    )

    print(
        "Clés ZIP + lat + lng    : "
        f"{'OK' if keys_ok else 'ERREUR'}"
    )

    if missing:

        print(
            "  Géolocalisations "
            f"manquantes : {len(missing)}"
        )

    if extra:

        print(
            "  Géolocalisations "
            f"supplémentaires : {len(extra)}"
        )

    return (
        count_ok
        and keys_ok
    )


# ============================================================
# 7. TRADUCTIONS DES CATÉGORIES
# ============================================================

def check_category_translations(
    db,
    expected,
):

    print("\n" + "=" * 60)
    print(
        "7. TRADUCTIONS DES CATÉGORIES"
    )
    print("=" * 60)

    translations = (
        expected["translations"]
    )

    translation_map = {}

    # --------------------------------------------------------
    # Création du dictionnaire de traduction
    # --------------------------------------------------------

    for _, row in translations.iterrows():

        portuguese = normalize_text(
            row[
                "product_category_name"
            ]
        )

        english = normalize_text(
            row[
                "product_category_name_english"
            ]
        )

        if portuguese:
            translation_map[
                portuguese
            ] = english

    total_products = 0

    missing_translation = 0

    incorrect_translation = 0

    errors = []

    # --------------------------------------------------------
    # Produits MongoDB
    # --------------------------------------------------------

    cursor = db.products.find(
        {},
        {
            "product_id": 1,
            "category.name": 1,
            "category.name_en": 1,
        },
    )

    for product in cursor:

        total_products += 1

        product_id = product.get(
            "product_id"
        )

        category = product.get(
            "category",
            {},
        )

        category_name = normalize_text(
            category.get("name")
        )

        category_name_en = normalize_text(
            category.get("name_en")
        )

        # ----------------------------------------------------
        # CATÉGORIE UNKNOWN
        # ----------------------------------------------------
        #
        # Le cleaner.py transforme une catégorie absente
        # en "unknown".
        #
        # Le loader.py conserve ensuite "unknown" dans MongoDB.
        #
        # Nous devons donc considérer "unknown" comme une
        # valeur valide et attendue.
        # ----------------------------------------------------

        if category_name == "unknown":

            expected_translation = "unknown"

            if (
                category_name_en
                != expected_translation
            ):

                incorrect_translation += 1

                errors.append(
                    (
                        product_id,
                        category_name,
                        category_name_en,
                        expected_translation,
                    )
                )

            continue

        # ----------------------------------------------------
        # Catégorie absente du dictionnaire
        # ----------------------------------------------------

        if (
            category_name
            not in translation_map
        ):

            missing_translation += 1

            errors.append(
                (
                    product_id,
                    category_name,
                    category_name_en,
                    "TRADUCTION ABSENTE",
                )
            )

            continue

        # ----------------------------------------------------
        # Traduction attendue
        # ----------------------------------------------------

        expected_translation = (
            translation_map[
                category_name
            ]
        )

        # ----------------------------------------------------
        # Comparaison
        # ----------------------------------------------------

        if (
            category_name_en
            != expected_translation
        ):

            incorrect_translation += 1

            errors.append(
                (
                    product_id,
                    category_name,
                    category_name_en,
                    expected_translation,
                )
            )

    presence_ok = (
        missing_translation == 0
    )

    translation_ok = (
        incorrect_translation == 0
    )

    print(
        f"Produits contrôlés       : "
        f"{total_products}"
    )

    print(
        "category.name_en         : "
        f"{'OK' if presence_ok else 'ERREUR'}"
    )

    print(
        "Correspondance CSV       : "
        f"{'OK' if translation_ok else 'ERREUR'}"
    )

    if missing_translation:

        print(
            "  Traductions manquantes : "
            f"{missing_translation}"
        )

    if incorrect_translation:

        print(
            "  Traductions incorrectes : "
            f"{incorrect_translation}"
        )

    # --------------------------------------------------------
    # Détail des anomalies
    # --------------------------------------------------------

    if errors:

        print(
            "\nPremières anomalies :"
        )

        for error in errors[:10]:

            (
                product_id,
                category,
                actual,
                expected_value,
            ) = error

            print(
                f"  Produit : {product_id}"
            )

            print(
                f"    catégorie : {category}"
            )

            print(
                f"    MongoDB   : {actual}"
            )

            print(
                f"    Attendu   : {expected_value}"
            )

    return (
        presence_ok
        and translation_ok
    )


# ============================================================
# 8. STRUCTURE D'UNE COMMANDE
# ============================================================

def check_order_structure(db):

    print("\n" + "=" * 60)
    print("8. STRUCTURE D'UNE COMMANDE")
    print("=" * 60)

    order = db.orders.find_one()

    if not order:

        print(
            "Aucune commande trouvée."
        )

        return False

    print(
        f"order_id    : "
        f"{order.get('order_id')}"
    )

    print(
        f"customer_id : "
        f"{order.get('customer_id')}"
    )

    print(
        f"status      : "
        f"{order.get('status')}"
    )

    print(
        f"items       : "
        f"{len(order.get('items', []))}"
    )

    print(
        f"payments    : "
        f"{len(order.get('payments', []))}"
    )

    print(
        f"reviews     : "
        f"{len(order.get('reviews', []))}"
    )

    print(
        f"dates       : "
        f"{list(order.get('dates', {}).keys())}"
    )

    return True


# ============================================================
# 9. RÉSUMÉ
# ============================================================

def print_summary(db):

    print("\n" + "=" * 60)
    print("9. RÉSUMÉ MONGODB")
    print("=" * 60)

    collections = [
        "customers",
        "products",
        "sellers",
        "orders",
        "geolocations",
    ]

    for collection_name in collections:

        count = (
            db[collection_name]
            .count_documents({})
        )

        print(
            f"{collection_name:<15}: "
            f"{count}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("VÉRIFICATION OLIST → MONGODB")
    print("=" * 60)

    print(
        f"Mode de vérification : "
        f"{LOAD_MODE}"
    )

    if LOAD_MODE == "TEST":

        print(
            f"Commandes attendues : "
            f"{TEST_ORDER_LIMIT}"
        )

    expected = (
        load_expected_data()
    )

    client, db = get_database()

    print(
        f"\nConnexion MongoDB OK : "
        f"{MONGO_DATABASE}"
    )

    try:

        results = []

        results.append(
            check_collection_counts(
                db,
                expected,
            )
        )

        results.append(
            check_embedded_data(
                db,
                expected,
            )
        )

        results.append(
            check_ids(
                db,
                expected,
            )
        )

        results.append(
            check_references(db)
        )

        results.append(
            check_indexes(db)
        )

        results.append(
            check_geolocations(
                db,
                expected,
            )
        )

        results.append(
            check_category_translations(
                db,
                expected,
            )
        )

        results.append(
            check_order_structure(db)
        )

        print_summary(db)

        print("\n" + "=" * 60)

        if all(results):

            print(
                "VÉRIFICATION GLOBALE : OK"
            )

            print(
                "La base MongoDB est cohérente "
                "avec le mode de chargement."
            )

        else:

            print(
                "VÉRIFICATION GLOBALE : ERREUR"
            )

            print(
                "Certaines vérifications "
                "nécessitent une correction."
            )

        print("=" * 60)

    finally:

        client.close()

        print(
            "\nConnexion MongoDB fermée."
        )


if __name__ == "__main__":
    main()