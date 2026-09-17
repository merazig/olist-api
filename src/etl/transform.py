"""Transforme les CSV en dict."""

import pandas as pd

import time


def orders_dict():
    """Cree le dict des ordres."""
    orders_mongo = []

    orders = pd.read_csv("data/proceed/orders_clean.csv")
    orders = orders.astype(object).where(pd.notna(orders), None)

    order_items = pd.read_csv("data/proceed/order_items_clean.csv")
    order_items = order_items.astype(object).where(pd.notna(order_items), None)

    order_payments = pd.read_csv("data/proceed/order_payments_clean.csv")
    order_payments = order_payments.astype(object).where(pd.notna(order_payments), None)

    order_reviews = pd.read_csv("data/proceed/order_reviews_clean.csv")
    order_reviews = order_reviews.astype(object).where(pd.notna(order_reviews), None)

    items_grouped = order_items.groupby("order_id")
    payments_grouped = order_payments.groupby("order_id")
    reviews_grouped = order_reviews.groupby("order_id")

    start = time.time()

    for _, order in orders.iterrows():
        order_id = order["order_id"]

        orders_obj = {
            "_id": order_id,
            "customer_id": order["customer_id"],
            "status": order["order_status"],
            "purchase_timestamp": order["order_purchase_timestamp"],
            "items": [],
            "payments": [],
            "reviews": [],
            "delivery": {
                "estimated_delivery": order["order_estimated_delivery_date"],
                "delivered_at": order["order_delivered_customer_date"],
            },
        }

        if order_id in items_grouped.groups:
            for _, item in items_grouped.get_group(order_id).iterrows():
                orders_obj["items"].append(
                    {
                        "product_id": item["product_id"],
                        "seller_id": item["seller_id"],
                        "price": float(item["price"]),
                        "freight_value": float(item["freight_value"]),
                    }
                )

        if order_id in payments_grouped.groups:
            for _, payment in payments_grouped.get_group(order_id).iterrows():
                orders_obj["payments"].append(
                    {
                        "type": payment["payment_type"],
                        "installments": int(payment["payment_installments"]),
                        "value": float(payment["payment_value"]),
                    }
                )

        if order_id in reviews_grouped.groups:
            for _, review in reviews_grouped.get_group(order_id).iterrows():
                orders_obj["reviews"].append(
                    {
                        "review_id": review["review_id"],
                        "score": int(review["review_score"]),
                        "comment_title": review["review_comment_title"],
                        "comment_message": review["review_comment_message"],
                        "creation_date": review["review_creation_date"],
                        "answer_timestamp": review["review_answer_timestamp"],
                    }
                )

        orders_mongo.append(orders_obj)

    print("reviews: ", round(time.time() - start, 2))

    return orders_mongo


def customers_dict():
    """Cree le dict des customers."""
    customers = pd.read_csv("data/proceed/customers_clean.csv", dtype=str)

    customers_mongo = []

    for _, customer in customers.iterrows():
        customer_doc = {
            "_id": customer["customer_id"],
            "customer_unique_id": customer["customer_unique_id"],
            "zip_code": int(customer["customer_zip_code_prefix"]),
            "city": customer["customer_city"],
            "state": customer["customer_state"],
        }

        customers_mongo.append(customer_doc)

    return customers_mongo


def products_dict():
    """Cree product dict."""
    products = pd.read_csv("data/proceed/products_clean.csv")
    products = products.astype(object).where(pd.notna(products), None)

    category_translation = pd.read_csv(
        "data/proceed/product_category_name_translation.csv", dtype=str
    )

    products = products.merge(category_translation, on="product_category_name", how="left")

    products_mongo = []

    for _, product in products.iterrows():
        product_doc = {
            "_id": product["product_id"],
            "category": product["product_category_name_english"],
            "name_length": product["product_name_lenght"],
            "description_length": product["product_description_lenght"],
            "photos_qty": product["product_photos_qty"],
            "weight_g": product["product_weight_g"],
            "dimensions": {
                "length_cm": product["product_length_cm"],
                "height_cm": product["product_height_cm"],
                "width_cm": product["product_width_cm"],
            },
        }

        products_mongo.append(product_doc)

    return products_mongo

def sellers_dict():
    """Cree sellers_dict."""
    sellers = pd.read_csv("data/proceed/sellers_clean.csv")
    
    sellers_mongo = []

    for _, seller in sellers.iterrows():
        seller_doc = {
            "_id": seller["seller_id"],
            "zip_code": seller["seller_zip_code_prefix"],
            "city": seller["seller_city"],
            "state": seller["seller_state"]
        }

        sellers_mongo.append(seller_doc)

    return sellers_mongo
    
