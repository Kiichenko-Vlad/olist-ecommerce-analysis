"""
main.py

Головний ETL-скрипт проєкту Olist.

Запуск: python main.py

Порядок завантаження (FK-залежності):
    Рівень 1 (незалежні): customers, products, sellers
    Рівень 2:             orders         (FK → customers)
    Рівень 3:             order_items    (FK → orders, products, sellers)
                          order_payments (FK → orders)
                          order_reviews  (FK → orders)
"""

import sys

from src.config import get_engine
from src.extractors import (
    read_customers,
    read_orders,
    read_order_items,
    read_order_payments,
    read_order_reviews,
    read_products,
    read_sellers,
    read_geolocation,
    read_category_translation,
)
from src.transformers import (
    clean_customers,
    clean_orders,
    clean_order_items,
    clean_order_payments,
    clean_order_reviews,
    clean_products,
    clean_sellers,
    clean_geolocation,
)
from src.validators import (
    validate_fk,
    validate_not_null,
    validate_unique,
    validate_score_range,
)
from src.loaders import upsert, verify_counts


def main() -> None:
    print("=" * 65)
    print("  OLIST ETL START")
    print("=" * 65)

    try:
        engine = get_engine()

        # ── EXTRACT ──────────────────────────────────────────────
        print("\n▶ EXTRACT: читання CSV")
        raw_customers = read_customers()
        raw_orders = read_orders()
        raw_order_items = read_order_items()
        raw_payments = read_order_payments()
        raw_reviews = read_order_reviews()
        raw_products = read_products()
        raw_sellers = read_sellers()
        raw_geo = read_geolocation()
        raw_translations = read_category_translation()

        # ── TRANSFORM ─────────────────────────────────────────────
        print("\n▶ TRANSFORM: чистка і трансформації")
        customers = clean_customers(raw_customers)
        products = clean_products(raw_products, raw_translations)
        sellers = clean_sellers(raw_sellers)
        orders = clean_orders(raw_orders)
        order_items = clean_order_items(raw_order_items)
        payments = clean_order_payments(raw_payments)
        reviews = clean_order_reviews(raw_reviews)
        geo = clean_geolocation(raw_geo)  # noqa: F841 — для Кроку 5

        # ── VALIDATE ──────────────────────────────────────────────
        print("\n▶ VALIDATE: перевірка PK, NOT NULL, FK")

        # UNIQUE (PK)
        validate_unique(customers, ["customer_id"], "customers")
        validate_unique(products, ["product_id"], "products")
        validate_unique(sellers, ["seller_id"], "sellers")
        validate_unique(orders, ["order_id"], "orders")
        validate_unique(order_items, ["order_id", "order_item_id"], "order_items")
        validate_unique(reviews, ["review_id"], "order_reviews")

        # NOT NULL
        validate_not_null(
            customers,
            ["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"],
            "customers",
        )
        validate_not_null(
            products,
            ["product_id", "category_name_english"],
            "products",
        )
        validate_not_null(
            sellers,
            ["seller_id", "zip_code_prefix", "city", "state"],
            "sellers",
        )
        validate_not_null(
            orders,
            ["order_id", "customer_id", "status", "purchased_at"],
            "orders",
        )
        validate_not_null(
            reviews,
            ["review_id", "order_id", "score"],
            "order_reviews",
        )

        # CHECK
        validate_score_range(reviews, "score", 1, 5, "order_reviews")

        # FK (referential integrity)
        orders = validate_fk(
            orders,
            "customer_id",
            customers,
            "customer_id",
            "orders",
            "customers",
        )
        order_items = validate_fk(
            order_items,
            "order_id",
            orders,
            "order_id",
            "order_items",
            "orders",
        )
        order_items = validate_fk(
            order_items,
            "product_id",
            products,
            "product_id",
            "order_items",
            "products",
        )
        order_items = validate_fk(
            order_items,
            "seller_id",
            sellers,
            "seller_id",
            "order_items",
            "sellers",
        )
        payments = validate_fk(
            payments,
            "order_id",
            orders,
            "order_id",
            "order_payments",
            "orders",
        )
        reviews = validate_fk(
            reviews,
            "order_id",
            orders,
            "order_id",
            "order_reviews",
            "orders",
        )

        # ── LOAD ──────────────────────────────────────────────────
        print("\n▶ LOAD: запис у PostgreSQL")

        # Рівень 1 — незалежні батьківські таблиці
        upsert(customers, "customers", ["customer_id"], engine)
        upsert(products, "products", ["product_id"], engine)
        upsert(sellers, "sellers", ["seller_id"], engine)

        # Рівень 2 — залежить від customers
        upsert(orders, "orders", ["order_id"], engine)

        # Рівень 3 — залежать від orders (і products/sellers)
        upsert(order_items, "order_items", ["order_id", "order_item_id"], engine)
        upsert(payments, "order_payments", ["order_id", "payment_sequential"], engine)
        upsert(reviews, "order_reviews", ["review_id"], engine)

        # ── VERIFY ────────────────────────────────────────────────
        verify_counts(
            {
                "customers": len(customers),
                "products": len(products),
                "sellers": len(sellers),
                "orders": len(orders),
                "order_items": len(order_items),
                "order_payments": len(payments),
                "order_reviews": len(reviews),
            },
            engine,
        )

        print("\n" + "=" * 65)
        print("  ✓ OLIST ETL SUCCESS")
        print("=" * 65)

    except Exception as e:
        print(f"\n  ✗ ETL FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
