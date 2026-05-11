"""
Читання всіх 9 CSV-файлів Olist у DataFrame.

Кожна функція:
- задає dtype для кожної колонки явно (не покладаємось на автовизначення)
- задає parse_dates для дат (щоб одразу отримати datetime64, а не string)
- задає na_values для нестандартних позначень NULL

Чистки тут немає — тільки "сирі" дані з правильними типами.
Чистка — в src/transformers.py.
"""

import pandas as pd
from .config import DATA_DIR

# ── Спільні константи ────────────────────────────────────────
# Винесені сюди окремо, щоб змінювати в одному місці, а не в 9 функціях.

_NA_VALUES: list[str] = ["", "N/A", "null", "NULL", "nan", "NaN"]
_ENCODING = "utf-8"


# ── Приватний хелпер ─────────────────────────────────────────


def _read_csv(
    filename: str,
    dtype: dict[str, str],
    parse_dates: list[str] | None = None,
) -> pd.DataFrame:
    """
    Єдина точка читання CSV.

    Усі спільні параметри (na_values, encoding) задані тут один раз.
    Публічні функції нижче лише описують *що* саме читати (dtype, дати),
    а *як* — делеговано сюди.
    """
    return pd.read_csv(
        DATA_DIR / filename,
        dtype=dtype,
        parse_dates=parse_dates or [],
        na_values=_NA_VALUES,
        encoding=_ENCODING,
    )


# ── Публічний API ────────────────────────────────────────────

__all__ = [
    "read_customers",
    "read_orders",
    "read_order_items",
    "read_order_payments",
    "read_order_reviews",
    "read_products",
    "read_sellers",
    "read_geolocation",
    "read_category_translation",
]


def read_customers() -> pd.DataFrame:
    """Клієнти. PK: customer_id (хеш-рядок)."""
    return _read_csv(
        "olist_customers_dataset.csv",
        dtype={
            "customer_id": "string",
            "customer_unique_id": "string",
            "customer_zip_code_prefix": "Int64",
            "customer_city": "string",
            "customer_state": "string",
        },
    )


def read_orders() -> pd.DataFrame:
    """Замовлення. PK: order_id. 5 полів-дат (ISO-формат)."""
    return _read_csv(
        "olist_orders_dataset.csv",
        dtype={
            "order_id": "string",
            "customer_id": "string",
            "order_status": "string",
        },
        parse_dates=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )


def read_order_items() -> pd.DataFrame:
    """Позиції замовлень. Composite PK: (order_id, order_item_id)."""
    return _read_csv(
        "olist_order_items_dataset.csv",
        dtype={
            "order_id": "string",
            "order_item_id": "Int64",
            "product_id": "string",
            "seller_id": "string",
            "price": "float64",
            "freight_value": "float64",
        },
        parse_dates=["shipping_limit_date"],
    )


def read_order_payments() -> pd.DataFrame:
    """Платежі. Одне замовлення може мати декілька рядків."""
    return _read_csv(
        "olist_order_payments_dataset.csv",
        dtype={
            "order_id": "string",
            "payment_sequential": "Int64",
            "payment_type": "string",
            "payment_installments": "Int64",
            "payment_value": "float64",
        },
    )


def read_order_reviews() -> pd.DataFrame:
    """
    Відгуки. PK: review_id.

    ~60 % NULL у comment_title / comment_message — це норма,
    не всі покупці залишають текст.
    """
    return _read_csv(
        "olist_order_reviews_dataset.csv",
        dtype={
            "review_id": "string",
            "order_id": "string",
            "review_score": "Int64",
            "review_comment_title": "string",
            "review_comment_message": "string",
        },
        parse_dates=[
            "review_creation_date",
            "review_answer_timestamp",
        ],
    )


def read_products() -> pd.DataFrame:
    """
    Каталог товарів. PK: product_id.

    ~1 % NULL у weight/length/height/width — заповнюються у transformers.
    """
    return _read_csv(
        "olist_products_dataset.csv",
        dtype={
            "product_id": "string",
            "product_category_name": "string",
            "product_name_lenght": "Int64",
            "product_description_lenght": "Int64",
            "product_photos_qty": "Int64",
            "product_weight_g": "Int64",
            "product_length_cm": "Int64",
            "product_height_cm": "Int64",
            "product_width_cm": "Int64",
        },
    )


def read_sellers() -> pd.DataFrame:
    """Продавці. PK: seller_id. Пропусків за EDA немає."""
    return _read_csv(
        "olist_sellers_dataset.csv",
        dtype={
            "seller_id": "string",
            "seller_zip_code_prefix": "Int64",
            "seller_city": "string",
            "seller_state": "string",
        },
    )


def read_geolocation() -> pd.DataFrame:
    """
    Геолокація. Дублікати по zip-коду — агрегуються у transformers.

    НЕ завантажується в БД — використовується як довідник.
    """
    return _read_csv(
        "olist_geolocation_dataset.csv",
        dtype={
            "geolocation_zip_code_prefix": "Int64",
            "geolocation_city": "string",
            "geolocation_state": "string",
        },
    )


def read_category_translation() -> pd.DataFrame:
    """Переклад категорій (порт. → англ.). Для merge у transformers."""
    return _read_csv(
        "product_category_name_translation.csv",
        dtype={
            "product_category_name": "string",
            "product_category_name_english": "string",
        },
    )
