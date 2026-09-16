from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def clean_zip_code(series: pd.Series) -> pd.Series:
    """
    Nettoie les codes postaux en conservant toujours 5 caractères.

    Exemple :
        1000   -> 01000
        14409  -> 14409
        01000  -> 01000
    """
    return (
        series
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(5)
    )


def clean_city(series: pd.Series) -> pd.Series:
    """Nettoie les noms de villes."""
    return series.astype("string").str.strip().str.lower()


def clean_state(series: pd.Series) -> pd.Series:
    """Nettoie les codes d'État."""
    return series.astype("string").str.strip().str.upper()


def clean_numeric_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> None:
    """Convertit les colonnes indiquées en valeurs numériques."""
    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )


def clean_date_columns(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> None:
    """Convertit les colonnes indiquées en dates."""
    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = pd.to_datetime(
                dataframe[column],
                errors="coerce",
            )


def save_csv(dataframe: pd.DataFrame, filename: str) -> None:
    """Sauvegarde un DataFrame dans data/processed."""
    output_path = PROCESSED_DIR / filename
    dataframe.to_csv(output_path, index=False)
    print(f"Fichier créé : {output_path.name}")


# ============================================================
# CUSTOMERS
# ============================================================

def clean_customers() -> pd.DataFrame:
    """Nettoie le fichier customers."""
    path = RAW_DIR / "olist_customers_dataset.csv"

    df = pd.read_csv(path)

    df["customer_id"] = df["customer_id"].astype("string").str.strip()
    df["customer_unique_id"] = (
        df["customer_unique_id"].astype("string").str.strip()
    )

    # IMPORTANT : conserver les zéros initiaux
    df["customer_zip_code_prefix"] = clean_zip_code(
        df["customer_zip_code_prefix"]
    )

    df["customer_city"] = clean_city(df["customer_city"])
    df["customer_state"] = clean_state(df["customer_state"])

    df = df.drop_duplicates(subset=["customer_id"])

    save_csv(df, "customers.csv")

    return df


# ============================================================
# ORDERS
# ============================================================

def clean_orders() -> pd.DataFrame:
    """Nettoie le fichier orders."""
    path = RAW_DIR / "olist_orders_dataset.csv"

    df = pd.read_csv(path)

    df["order_id"] = df["order_id"].astype("string").str.strip()
    df["customer_id"] = df["customer_id"].astype("string").str.strip()
    df["order_status"] = df["order_status"].astype("string").str.strip()

    clean_date_columns(
        df,
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    df = df.drop_duplicates(subset=["order_id"])

    save_csv(df, "orders.csv")

    return df


# ============================================================
# ORDER ITEMS
# ============================================================

def clean_order_items() -> pd.DataFrame:
    """Nettoie le fichier order_items."""
    path = RAW_DIR / "olist_order_items_dataset.csv"

    df = pd.read_csv(path)

    df["order_id"] = df["order_id"].astype("string").str.strip()
    df["product_id"] = df["product_id"].astype("string").str.strip()
    df["seller_id"] = df["seller_id"].astype("string").str.strip()

    clean_numeric_columns(
        df,
        [
            "order_item_id",
            "price",
            "freight_value",
        ],
    )

    clean_date_columns(
        df,
        ["shipping_limit_date"],
    )

    save_csv(df, "order_items.csv")

    return df


# ============================================================
# PAYMENTS
# ============================================================

def clean_payments() -> pd.DataFrame:
    """Nettoie le fichier payments."""
    path = RAW_DIR / "olist_order_payments_dataset.csv"

    df = pd.read_csv(path)

    df["order_id"] = df["order_id"].astype("string").str.strip()
    df["payment_type"] = (
        df["payment_type"].astype("string").str.strip()
    )

    clean_numeric_columns(
        df,
        [
            "payment_sequential",
            "payment_installments",
            "payment_value",
        ],
    )

    save_csv(df, "payments.csv")

    return df


# ============================================================
# REVIEWS
# ============================================================

def clean_reviews() -> pd.DataFrame:
    """Nettoie le fichier reviews."""
    path = RAW_DIR / "olist_order_reviews_dataset.csv"

    df = pd.read_csv(path)

    df["review_id"] = df["review_id"].astype("string").str.strip()
    df["order_id"] = df["order_id"].astype("string").str.strip()

    # Les commentaires manquants deviennent des chaînes vides
    df["review_comment_title"] = (
        df["review_comment_title"]
        .fillna("")
        .astype("string")
        .str.strip()
    )

    df["review_comment_message"] = (
        df["review_comment_message"]
        .fillna("")
        .astype("string")
        .str.strip()
    )

    clean_numeric_columns(
        df,
        ["review_score"],
    )

    clean_date_columns(
        df,
        [
            "review_creation_date",
            "review_answer_timestamp",
        ],
    )

    save_csv(df, "reviews.csv")

    return df


# ============================================================
# PRODUCTS
# ============================================================

def clean_products() -> pd.DataFrame:
    """Nettoie le fichier products."""
    path = RAW_DIR / "olist_products_dataset.csv"

    df = pd.read_csv(path)

    df["product_id"] = df["product_id"].astype("string").str.strip()

    df["product_category_name"] = (
        df["product_category_name"]
        .fillna("unknown")
        .astype("string")
        .str.strip()
    )

    clean_numeric_columns(
        df,
        [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    )

    df = df.drop_duplicates(subset=["product_id"])

    save_csv(df, "products.csv")

    return df


# ============================================================
# SELLERS
# ============================================================

def clean_sellers() -> pd.DataFrame:
    """Nettoie le fichier sellers."""
    path = RAW_DIR / "olist_sellers_dataset.csv"

    df = pd.read_csv(path)

    df["seller_id"] = df["seller_id"].astype("string").str.strip()

    # IMPORTANT : conserver les zéros initiaux
    df["seller_zip_code_prefix"] = clean_zip_code(
        df["seller_zip_code_prefix"]
    )

    df["seller_city"] = clean_city(df["seller_city"])
    df["seller_state"] = clean_state(df["seller_state"])

    df = df.drop_duplicates(subset=["seller_id"])

    save_csv(df, "sellers.csv")

    return df


# ============================================================
# GEOLOCATION
# ============================================================

def clean_geolocation() -> pd.DataFrame:
    """Nettoie le fichier geolocation."""
    path = RAW_DIR / "olist_geolocation_dataset.csv"

    df = pd.read_csv(path)

    # IMPORTANT : conserver les zéros initiaux
    df["geolocation_zip_code_prefix"] = clean_zip_code(
        df["geolocation_zip_code_prefix"]
    )

    df["geolocation_city"] = clean_city(
        df["geolocation_city"]
    )

    df["geolocation_state"] = clean_state(
        df["geolocation_state"]
    )

    clean_numeric_columns(
        df,
        [
            "geolocation_lat",
            "geolocation_lng",
        ],
    )

    save_csv(df, "geolocation.csv")

    return df


# ============================================================
# CATEGORY TRANSLATION
# ============================================================

def clean_category_translation() -> pd.DataFrame:
    """Nettoie la traduction des catégories."""
    path = RAW_DIR / "product_category_name_translation.csv"

    df = pd.read_csv(path)

    df["product_category_name"] = (
        df["product_category_name"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    df["product_category_name_english"] = (
        df["product_category_name_english"]
        .astype("string")
        .str.strip()
        .str.lower()
    )

    save_csv(df, "category_translation.csv")

    return df


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    """Nettoie l'ensemble des fichiers Olist."""

    print("=" * 60)
    print("NETTOYAGE DU DATASET OLIST")
    print("=" * 60)

    clean_customers()
    clean_orders()
    clean_order_items()
    clean_payments()
    clean_reviews()
    clean_products()
    clean_sellers()
    clean_geolocation()
    clean_category_translation()

    print()
    print("=" * 60)
    print("NETTOYAGE DU DATASET OLIST TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    main()