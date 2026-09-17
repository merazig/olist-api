"""Main."""

from src.etl.clean_csv import (
    clean_orders,
    clean_order_items,
    clean_order_reviews,
    clean_order_payments,
    clean_customers,
    clean_category_translation,
    clean_products,
    clean_sellers,
)

from src.etl.transform import orders_dict, customers_dict, products_dict, sellers_dict

from src.etl.load_mongo import get_database, load_to_mongo

import time


def main():
    """Main."""
    # clean csv
    clean_orders()
    clean_order_items()
    clean_order_reviews()
    clean_order_payments()
    clean_customers()
    clean_category_translation()
    clean_products()
    clean_sellers()

    # Connect to mongodb
    db = get_database()

    # transform order
    print("======Orders======")
    start = time.time()
    orders = orders_dict()
    end = time.time()
    print("temps de creation de dict orders: ", round((end - start), 2))

    # load orders
    start = time.time()
    load_to_mongo(db, "orders", orders)
    end = time.time()
    print("temps de load des données orders: ", round((end - start), 2))

    # transform and customers
    print("======Customers======")
    start = time.time()
    customers = customers_dict()
    load_to_mongo(db, "customers", customers)
    end = time.time()
    print("temps de transform et load des customers: ", round((end - start), 2))

    print("======Products======")
    start = time.time()
    products = products_dict()
    load_to_mongo(db, "products", products)
    end = time.time()
    print("temps de transform et load des products: ", round((end - start), 2))

    print("======Sellers======")
    start = time.time()
    sellers = sellers_dict()
    load_to_mongo(db, "sellers", sellers)
    end = time.time()
    print("temps de transform et load des sellers: ", round((end - start), 2))


if __name__ == "__main__":
    main()
