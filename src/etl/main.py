"""Main."""

from src.etl.clean_csv import (
    clean_orders,
    clean_order_items,
    clean_order_reviews,
    clean_order_payments,
    clean_customers,
    clean_category_translation,
    clean_products,
    clean_sellers
)

from src.etl.transform import (
    orders_dict,
    customers_dict,
    products_dict,
    sellers_dict
)

from src.etl.load_mongo import (
    get_database,
    load_to_mongo
)

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
    orders = orders_dict()
    
    # load orders
    load_to_mongo(db, "orders", orders)

    # transform and customers
    customers = customers_dict()
    load_to_mongo(db, "customers", customers)
    
    products = products_dict()
    load_to_mongo(db, "products", products)
    
    sellers = sellers_dict()
    load_to_mongo(db, "sellers", sellers)
    
if __name__=="__main__":
    main()