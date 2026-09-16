from pathlib import Path

import pandas as pd


DATA_DIR = Path("data/raw")


def load_data() -> dict[str, pd.DataFrame]:
    """Charge les fichiers nécessaires au profilage des relations."""
    return {
        "customers": pd.read_csv(
            DATA_DIR / "olist_customers_dataset.csv"
        ),
        "orders": pd.read_csv(
            DATA_DIR / "olist_orders_dataset.csv"
        ),
        "items": pd.read_csv(
            DATA_DIR / "olist_order_items_dataset.csv"
        ),
        "products": pd.read_csv(
            DATA_DIR / "olist_products_dataset.csv"
        ),
        "sellers": pd.read_csv(
            DATA_DIR / "olist_sellers_dataset.csv"
        ),
        "payments": pd.read_csv(
            DATA_DIR / "olist_order_payments_dataset.csv"
        ),
        "reviews": pd.read_csv(
            DATA_DIR / "olist_order_reviews_dataset.csv"
        ),
    }


def check_uniqueness(
    df: pd.DataFrame,
    column: str,
    label: str,
) -> None:
    """Vérifie l'unicité d'une clé."""
    duplicates = df[column].duplicated().sum()

    print(f"{label:<45} {duplicates} doublon(s)")


def check_relation(
    child: pd.DataFrame,
    parent: pd.DataFrame,
    child_key: str,
    parent_key: str,
    relation: str,
) -> None:
    """Vérifie les clés étrangères orphelines."""
    valid_keys = parent[parent_key].dropna().unique()

    orphan_count = (~child[child_key].isin(valid_keys)).sum()

    print(f"{relation:<45} {orphan_count} orphelin(s)")


def cardinality(
    df: pd.DataFrame,
    group_key: str,
    relation_name: str,
) -> None:
    """Analyse le nombre d'enregistrements par entité."""
    counts = df.groupby(group_key).size()

    print(f"\n{relation_name}")
    print(f"  Minimum : {counts.min()}")
    print(f"  Maximum : {counts.max()}")
    print(f"  Moyenne : {counts.mean():.2f}")
    print(f"  Médiane : {counts.median():.2f}")


def profile_customers(data: dict[str, pd.DataFrame]) -> None:
    """Profile les relations clients-commandes."""
    customers = data["customers"]
    orders = data["orders"]

    print("\n" + "=" * 80)
    print("1. CLIENTS")
    print("=" * 80)

    check_uniqueness(
        customers,
        "customer_id",
        "customers.customer_id",
    )

    check_uniqueness(
        customers,
        "customer_unique_id",
        "customers.customer_unique_id",
    )

    check_relation(
        orders,
        customers,
        "customer_id",
        "customer_id",
        "orders.customer_id -> customers.customer_id",
    )

    cardinality(
        orders,
        "customer_id",
        "Nombre de commandes par customer_id",
    )

    mapping = customers.groupby("customer_unique_id")[
        "customer_id"
    ].nunique()

    print("\ncustomer_unique_id -> customer_id")
    print(f"  Maximum : {mapping.max()}")
    print(f"  Moyenne : {mapping.mean():.2f}")
    print(
        f"  Plusieurs customer_id : "
        f"{(mapping > 1).sum()}"
    )


def profile_orders(data: dict[str, pd.DataFrame]) -> None:
    """Profile les relations liées aux commandes."""
    orders = data["orders"]
    items = data["items"]
    payments = data["payments"]
    reviews = data["reviews"]

    print("\n" + "=" * 80)
    print("2. COMMANDES")
    print("=" * 80)

    check_uniqueness(
        orders,
        "order_id",
        "orders.order_id",
    )

    check_relation(
        items,
        orders,
        "order_id",
        "order_id",
        "items.order_id -> orders.order_id",
    )

    check_relation(
        payments,
        orders,
        "order_id",
        "order_id",
        "payments.order_id -> orders.order_id",
    )

    check_relation(
        reviews,
        orders,
        "order_id",
        "order_id",
        "reviews.order_id -> orders.order_id",
    )

    cardinality(
        items,
        "order_id",
        "Nombre d'articles par commande",
    )

    cardinality(
        payments,
        "order_id",
        "Nombre de paiements par commande",
    )

    cardinality(
        reviews,
        "order_id",
        "Nombre d'avis par commande",
    )


def profile_items(data: dict[str, pd.DataFrame]) -> None:
    """Profile les relations articles-produits-vendeurs."""
    items = data["items"]
    products = data["products"]
    sellers = data["sellers"]

    print("\n" + "=" * 80)
    print("3. ARTICLES / PRODUITS / VENDEURS")
    print("=" * 80)

    check_relation(
        items,
        products,
        "product_id",
        "product_id",
        "items.product_id -> products.product_id",
    )

    check_relation(
        items,
        sellers,
        "seller_id",
        "seller_id",
        "items.seller_id -> sellers.seller_id",
    )

    cardinality(
        items,
        "product_id",
        "Nombre de ventes par produit",
    )

    cardinality(
        items,
        "seller_id",
        "Nombre d'articles par vendeur",
    )


def main() -> None:
    """Exécute le profilage complet du dataset Olist."""
    data = load_data()

    profile_customers(data)
    profile_orders(data)
    profile_items(data)


if __name__ == "__main__":
    main()