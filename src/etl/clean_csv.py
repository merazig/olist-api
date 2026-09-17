"""Fonctions de nettoyage des fichiers CSV du dataset Olist.

Ce module contient les fonctions responsables de la préparation
des données avant leur transformation en documents MongoDB.
"""

import pandas as pd


def clean_customers():
    """Nettoie et prépare les données du fichier customers."""
    df = pd.read_csv("data/raw/olist_customers_dataset.csv")

    df = df.drop_duplicates(subset=["customer_id"])

    df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].astype(str).str.zfill(5)

    df.to_csv("data/proceed/customers_clean.csv", index=False)


def clean_orders():
    """Nettoie et prépare les données du fichier orders."""
    df = pd.read_csv("data/raw/olist_orders_dataset.csv")

    df = df.drop_duplicates(subset=["order_id"])

    df.to_csv("data/proceed/orders_clean.csv", index=False)


def clean_order_items():
    """Nettoie et prépare les données du fichier order_items."""
    df = pd.read_csv("data/raw/olist_order_items_dataset.csv")

    # Supprime les doublons en se basant uniquement sur la commande et le numéro de l'article
    df = df.drop_duplicates(subset=["order_id", "order_item_id"], keep="first")

    df.to_csv("data/proceed/order_items_clean.csv", index=False)


def clean_order_payments():
    """Nettoie et prépare les données du fichier order_payments."""
    df = pd.read_csv("data/raw/olist_order_payments_dataset.csv")

    df = df.drop_duplicates()

    df.to_csv("data/proceed/order_payments_clean.csv", index=False)


def clean_order_reviews():
    """Nettoie et prépare les données du fichier order_reviews."""
    df = pd.read_csv("data/raw/olist_order_reviews_dataset.csv")

    df = df.drop_duplicates()

    df.to_csv("data/proceed/order_reviews_clean.csv", index=False)


def clean_products():
    """Nettoie et prépare les données du fichier products."""
    df = pd.read_csv("data/raw/olist_products_dataset.csv")

    df = df.drop_duplicates()

    df.to_csv("data/proceed/products_clean.csv", index=False)


def clean_sellers():
    """Nettoie et prépare les données du fichier sellers."""
    df = pd.read_csv("data/raw/olist_sellers_dataset.csv")

    df = df.drop_duplicates()

    df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype(str).str.zfill(5)

    df.to_csv("data/proceed/sellers_clean.csv", index=False)


def clean_category_translation():
    """Nettoie et prépare les données de traduction des catégories."""
    df = pd.read_csv("data/raw/product_category_name_translation.csv")

    df = df.drop_duplicates()

    df.to_csv("data/proceed/product_category_name_translation.csv", index=False)
