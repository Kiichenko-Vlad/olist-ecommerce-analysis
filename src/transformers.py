"""
src/transformers.py

Трансформації для кожної з 7 таблиць Olist.

Кожна функція clean_*():
1. Приймає сирий DataFrame з extractors.py
2. Видаляє рядки з NULL у критичних (PK/FK) полях
3. Перейменовує колонки відповідно до схеми БД
4. Відкидає зайві колонки
5. Виправляє проблеми знайдені в EDA (NULL, дублікати, діапазони)
6. Повертає DataFrame тільки з колонками БД у правильних типах

Порядок дій всередині кожної функції:
    1. dropna(subset=[pk]) — критичні поля
    2. rename(columns={...}) — під схему БД
    3. drop(columns=[...]) — зайві колонки
    4. бізнес-логіка (заповнення NULL, перевірка діапазонів, дат)
    5. drop_duplicates(subset=[pk]) — дедуплікація по PK
    6. assert — фінальна перевірка цілісності
    7. return df[[ordered_columns]] — явний порядок колонок
"""

import pandas as pd


# ── Приватні хелпери ─────────────────────────────────────────
# Винесені з clean_*(), щоб не копіювати один і той самий
# патерн «порахуй → відфільтруй → виведи» 20 разів.


def _drop_nulls(df: pd.DataFrame, subset: list[str], table: str) -> pd.DataFrame:
    """Видаляє рядки з NULL у критичних полях і виводить кількість."""
    before = len(df)
    df = df.dropna(subset=subset)
    if dropped := before - len(df):
        print(f"  [{table}] Відкинуто {dropped} рядків з NULL у {subset}")
    return df


def _dedup(df: pd.DataFrame, subset: list[str], table: str) -> pd.DataFrame:
    """Дедуплікація по PK/composite PK, залишає перший запис."""
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    if dropped := before - len(df):
        print(f"  [{table}] Видалено {dropped} дублів по {subset}")
    return df


def _filter(
    df: pd.DataFrame,
    mask: pd.Series,
    table: str,
    reason: str,
) -> pd.DataFrame:
    """Залишає лише рядки де mask == True, виводить відкинуті."""
    before = len(df)
    df = df[mask]
    if dropped := before - len(df):
        print(f"  [{table}] Відкинуто {dropped} рядків: {reason}")
    return df


def _fill_nulls_by_category(
    df: pd.DataFrame,
    columns: list[str],
    category_col: str,
    table: str,
) -> pd.DataFrame:
    """
    Заповнює NULL медіаною по категорії, потім глобальною медіаною.

    Чому медіана по категорії, а не глобальна?
    Смартфон і матрац мають кардинально різні ваги/розміри —
    глобальна медіана дала б безглузді значення.

    Чому медіана, а не середнє?
    Медіана стійка до викидів — один товар з помилковою вагою 99999
    не зіпсує заповнення для всієї категорії.
    """
    for col in columns:
        null_count = df[col].isna().sum()
        if null_count == 0:
            continue
        category_medians = df.groupby(category_col)[col].transform("median")
        global_median = df[col].median()
        df[col] = df[col].fillna(category_medians).fillna(global_median)
        print(f"  [{table}] {col}: заповнено {null_count} NULL медіаною по категорії")
    return df


# ── Публічний API ────────────────────────────────────────────

__all__ = [
    "clean_customers",
    "clean_orders",
    "clean_order_items",
    "clean_order_payments",
    "clean_order_reviews",
    "clean_products",
    "clean_sellers",
    "clean_geolocation",
]


# ══════════════════════════════════════════════════
# CUSTOMERS
# ══════════════════════════════════════════════════


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_customers_dataset.csv → таблиця customers.

    Перейменування:
        customer_zip_code_prefix → zip_code_prefix
        customer_city            → city
        customer_state           → state

    Залишаємо всі 5 колонок — всі входять до схеми БД.
    Чистка: нормалізація тексту (lowercase city, uppercase state),
    zip_code_prefix → рядок з ведучими нулями (01310, а не 1310).

    Args:
        df: сирий DataFrame з read_customers().

    Returns:
        DataFrame з колонками:
        customer_id | customer_unique_id | zip_code_prefix | city | state
    """
    df = df.copy()

    df = _drop_nulls(df, ["customer_id"], "customers")

    df = df.rename(
        columns={
            "customer_zip_code_prefix": "zip_code_prefix",
            "customer_city": "city",
            "customer_state": "state",
        }
    )

    df["city"] = df["city"].str.strip().str.lower()
    df["state"] = df["state"].str.strip().str.upper()
    df["zip_code_prefix"] = df["zip_code_prefix"].astype(str).str.zfill(5)

    df = _dedup(df, ["customer_id"], "customers")

    assert df["customer_id"].notna().all(), "customers: є NULL у customer_id!"
    assert df["customer_id"].is_unique, "customers: customer_id не унікальний!"

    print(f"  [customers] ✓ Готово: {len(df):,} рядків")
    return df[["customer_id", "customer_unique_id", "zip_code_prefix", "city", "state"]]


# ══════════════════════════════════════════════════
# ORDERS
# ══════════════════════════════════════════════════


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_orders_dataset.csv → таблиця orders.

    Перейменування:
        order_status                   → status
        order_purchase_timestamp       → purchased_at
        order_approved_at              → approved_at
        order_delivered_carrier_date   → delivered_to_carrier_at
        order_delivered_customer_date  → delivered_to_customer_at
        order_estimated_delivery_date  → estimated_delivery_at

    Всі 8 колонок CSV входять до схеми БД — нічого не відкидаємо.

    Чистка:
        - Перевірка логіки дат: delivered_to_customer_at >= purchased_at.
        - ~3% NULL у delivered_to_customer_at — норма (ще не доставлені),
          не видаляємо.

    Args:
        df: сирий DataFrame з read_orders().

    Returns:
        DataFrame з колонками:
        order_id | customer_id | status | purchased_at | approved_at |
        delivered_to_carrier_at | delivered_to_customer_at | estimated_delivery_at
    """
    df = df.copy()

    df = _drop_nulls(
        df, ["order_id", "customer_id", "order_purchase_timestamp"], "orders"
    )

    df = df.rename(
        columns={
            "order_status": "status",
            "order_purchase_timestamp": "purchased_at",
            "order_approved_at": "approved_at",
            "order_delivered_carrier_date": "delivered_to_carrier_at",
            "order_delivered_customer_date": "delivered_to_customer_at",
            "order_estimated_delivery_date": "estimated_delivery_at",
        }
    )

    df["status"] = df["status"].str.strip().str.lower()

    # delivered_to_customer_at має бути ПІСЛЯ purchased_at (де не NULL)
    has_delivery = df["delivered_to_customer_at"].notna()
    valid_dates = ~has_delivery | (df["delivered_to_customer_at"] >= df["purchased_at"])
    df = _filter(df, valid_dates, "orders", "delivered < purchased")

    df = _dedup(df, ["order_id"], "orders")

    assert df["order_id"].notna().all(), "orders: є NULL у order_id!"
    assert df["order_id"].is_unique, "orders: order_id не унікальний!"
    assert df["customer_id"].notna().all(), "orders: є NULL у customer_id!"

    print(f"  [orders] ✓ Готово: {len(df):,} рядків")
    return df[
        [
            "order_id",
            "customer_id",
            "status",
            "purchased_at",
            "approved_at",
            "delivered_to_carrier_at",
            "delivered_to_customer_at",
            "estimated_delivery_at",
        ]
    ]


# ══════════════════════════════════════════════════
# ORDER ITEMS
# ══════════════════════════════════════════════════


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_order_items_dataset.csv → таблиця order_items.

    Всі 7 колонок CSV входять до схеми БД — нічого не відкидаємо
    і не перейменовуємо.

    Composite PK: (order_id, order_item_id).

    Чистка:
        - price > 0 (відповідає CHECK у DDL)
        - freight_value >= 0 (відповідає CHECK у DDL)
        - округлення до 2 знаків (відповідає DECIMAL(10,2) у БД)

    Args:
        df: сирий DataFrame з read_order_items().

    Returns:
        DataFrame з колонками:
        order_id | order_item_id | product_id | seller_id |
        shipping_limit_date | price | freight_value
    """
    df = df.copy()

    df = _drop_nulls(
        df, ["order_id", "order_item_id", "product_id", "seller_id"], "order_items"
    )
    df = _filter(df, df["price"] > 0, "order_items", "price <= 0")
    df = _filter(df, df["freight_value"] >= 0, "order_items", "freight_value < 0")

    df["price"] = df["price"].round(2)
    df["freight_value"] = df["freight_value"].round(2)
    df["order_item_id"] = df["order_item_id"].astype("Int64")

    df = _dedup(df, ["order_id", "order_item_id"], "order_items")

    assert (
        not df[["order_id", "order_item_id"]].duplicated().any()
    ), "order_items: composite PK не унікальний!"

    print(f"  [order_items] ✓ Готово: {len(df):,} рядків")
    return df[
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ]
    ]


# ══════════════════════════════════════════════════
# ORDER PAYMENTS
# ══════════════════════════════════════════════════


def clean_order_payments(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_order_payments_dataset.csv → таблиця order_payments.

    Перейменування:
        payment_installments → installments
        payment_value        → value

    Composite PK: (order_id, payment_sequential) — обидва залишаємо.
    Всі 5 колонок CSV входять до схеми БД.

    Чистка:
        - installments NULL → 0 (CHECK installments >= 0 у DDL)
        - value >= 0 (CHECK у DDL)
        - округлення до 2 знаків

    Примітка: одне замовлення може мати кілька рядків —
    різні способи оплати (credit_card + voucher) або розстрочки.

    Args:
        df: сирий DataFrame з read_order_payments().

    Returns:
        DataFrame з колонками:
        order_id | payment_sequential | payment_type | installments | value
    """
    df = df.copy()

    df = _drop_nulls(
        df,
        ["order_id", "payment_sequential", "payment_type", "payment_value"],
        "order_payments",
    )

    df = df.rename(
        columns={
            "payment_installments": "installments",
            "payment_value": "value",
        }
    )

    df = _filter(df, df["value"] >= 0, "order_payments", "value < 0")

    df["installments"] = df["installments"].fillna(0).astype("Int64")
    df["payment_sequential"] = df["payment_sequential"].astype("Int64")
    df["value"] = df["value"].round(2)

    print(f"  [order_payments] ✓ Готово: {len(df):,} рядків")
    return df[
        ["order_id", "payment_sequential", "payment_type", "installments", "value"]
    ]


# ══════════════════════════════════════════════════
# ORDER REVIEWS
# ══════════════════════════════════════════════════


def clean_order_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_order_reviews_dataset.csv → таблиця order_reviews.

    Перейменування:
        review_score            → score
        review_comment_title    → comment_title
        review_comment_message  → comment_message
        review_creation_date    → created_at
        review_answer_timestamp → answered_at

    Чистка: score ∈ [1, 5], strip текстових полів.

    ВАЖЛИВО: НЕ видаляємо рядки через NULL у comment_title/comment_message.
    ~88%/59% відгуків без тексту — це нормальна поведінка користувачів Olist.
    Ці колонки в БД визначені як nullable TEXT.

    Args:
        df: сирий DataFrame з read_order_reviews().

    Returns:
        DataFrame з колонками:
        review_id | order_id | score | comment_title |
        comment_message | created_at | answered_at
    """
    df = df.copy()

    df = _drop_nulls(df, ["review_id", "order_id", "review_score"], "order_reviews")

    df = df.rename(
        columns={
            "review_score": "score",
            "review_comment_title": "comment_title",
            "review_comment_message": "comment_message",
            "review_creation_date": "created_at",
            "review_answer_timestamp": "answered_at",
        }
    )

    df = _filter(df, df["score"].between(1, 5), "order_reviews", "score поза 1–5")

    df["score"] = df["score"].astype("Int64")
    df["comment_title"] = df["comment_title"].str.strip()
    df["comment_message"] = df["comment_message"].str.strip()

    df = _dedup(df, ["review_id"], "order_reviews")

    # Інформативний вивід — не помилка, а підтвердження що NULL очікувані
    print(
        f"  [order_reviews] comment_title NULL: "
        f"{df['comment_title'].isna().mean() * 100:.1f}% (норма)"
    )
    print(
        f"  [order_reviews] comment_message NULL: "
        f"{df['comment_message'].isna().mean() * 100:.1f}% (норма)"
    )

    assert df["review_id"].notna().all(), "order_reviews: є NULL у review_id!"
    assert df["review_id"].is_unique, "order_reviews: review_id не унікальний!"

    print(f"  [order_reviews] ✓ Готово: {len(df):,} рядків")
    return df[
        [
            "review_id",
            "order_id",
            "score",
            "comment_title",
            "comment_message",
            "created_at",
            "answered_at",
        ]
    ]


# ══════════════════════════════════════════════════
# PRODUCTS
# ══════════════════════════════════════════════════


def clean_products(
    df_products: pd.DataFrame,
    df_translation: pd.DataFrame,
) -> pd.DataFrame:
    """
    olist_products_dataset.csv + product_category_name_translation.csv
    → таблиця products.

    Ця функція приймає ДВА DataFrame і робить LEFT MERGE між ними.
    LEFT MERGE — зберігаємо всі продукти навіть якщо translation не знайдено.

    Перейменування:
        product_photos_qty → photos_qty
        product_weight_g   → weight_g
        product_length_cm  → length_cm
        product_height_cm  → height_cm
        product_width_cm   → width_cm

    Відкидаємо:
        product_category_name      (португальська — замінена англійською)
        product_name_lenght        (typo + не в схемі)
        product_description_lenght (typo + не в схемі)

    Чистка:
        category NULL → 'unknown' (перед merge!)
        розміри/вага NULL (~0.01%) → медіана по категорії
        photos_qty NULL → 0

    Args:
        df_products:    сирий DataFrame з read_products().
        df_translation: сирий DataFrame з read_category_translation().

    Returns:
        DataFrame з колонками:
        product_id | category_name_english | weight_g |
        length_cm | height_cm | width_cm | photos_qty
    """
    df = df_products.copy()

    # Заповнюємо NULL у category_name ДО merge —
    # щоб JOIN по 'unknown' теж спрацював коректно
    df["product_category_name"] = df["product_category_name"].fillna("unknown")

    # LEFT MERGE: додаємо англійські назви категорій
    df = df.merge(
        df_translation[["product_category_name", "product_category_name_english"]],
        on="product_category_name",
        how="left",
    )

    # Якщо після merge english_name = NULL (категорія не знайдена) → 'unknown'
    df["product_category_name_english"] = df["product_category_name_english"].fillna(
        "unknown"
    )

    # Розміри/вага: NULL → медіана по категорії
    df = _fill_nulls_by_category(
        df,
        columns=[
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        category_col="product_category_name_english",
        table="products",
    )

    # photos_qty NULL → 0 (немає фото — це валідний стан)
    df["product_photos_qty"] = df["product_photos_qty"].fillna(0)

    df = df.rename(
        columns={
            "product_category_name_english": "category_name_english",
            "product_photos_qty": "photos_qty",
            "product_weight_g": "weight_g",
            "product_length_cm": "length_cm",
            "product_height_cm": "height_cm",
            "product_width_cm": "width_cm",
        }
    )

    df = df.drop(
        columns=[
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
        ],
        errors="ignore",
    )

    for col in ["weight_g", "length_cm", "height_cm", "width_cm", "photos_qty"]:
        df[col] = df[col].round(0).astype("Int64")

    for col in ["weight_g", "length_cm", "height_cm", "width_cm"]:
        df[col] = df[col].clip(lower=1)

    df = _drop_nulls(df, ["product_id"], "products")
    df = _dedup(df, ["product_id"], "products")

    assert df["product_id"].notna().all(), "products: є NULL у product_id!"
    assert df["product_id"].is_unique, "products: product_id не унікальний!"

    print(f"  [products] ✓ Готово: {len(df):,} рядків")
    return df[
        [
            "product_id",
            "category_name_english",
            "weight_g",
            "length_cm",
            "height_cm",
            "width_cm",
            "photos_qty",
        ]
    ]


# ══════════════════════════════════════════════════
# SELLERS
# ══════════════════════════════════════════════════


def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_sellers_dataset.csv → таблиця sellers.

    Перейменування:
        seller_zip_code_prefix → zip_code_prefix
        seller_city            → city
        seller_state           → state

    Всі 4 колонки CSV входять до схеми БД — нічого не відкидаємо.
    Чистка: нормалізація тексту (lowercase city, uppercase state).

    Args:
        df: сирий DataFrame з read_sellers().

    Returns:
        DataFrame з колонками: seller_id | zip_code_prefix | city | state
    """
    df = df.copy()

    df = _drop_nulls(df, ["seller_id"], "sellers")

    df = df.rename(
        columns={
            "seller_zip_code_prefix": "zip_code_prefix",
            "seller_city": "city",
            "seller_state": "state",
        }
    )

    df["city"] = df["city"].str.strip().str.lower()
    df["state"] = df["state"].str.strip().str.upper()
    df["zip_code_prefix"] = df["zip_code_prefix"].astype(str).str.zfill(5)

    df = _dedup(df, ["seller_id"], "sellers")

    assert df["seller_id"].notna().all(), "sellers: є NULL у seller_id!"
    assert df["seller_id"].is_unique, "sellers: seller_id не унікальний!"

    print(f"  [sellers] ✓ Готово: {len(df):,} рядків")
    return df[["seller_id", "zip_code_prefix", "city", "state"]]


# ══════════════════════════════════════════════════
# GEOLOCATION (агрегація — не завантажується в БД)
# ══════════════════════════════════════════════════


def clean_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    """
    olist_geolocation_dataset.csv → агрегований довідник (~15k рядків).

    Проблема: ~1 млн рядків, але тільки ~15k унікальних zip-кодів.
    На один zip — десятки GPS-точок (різні вулиці одного поштового індексу).

    Рішення: groupby zip_code + agg(median) → 1 точка на zip.
    Медіана краща за mean — стійка до outliers (хибних координат).

    Результат НЕ завантажується в основні таблиці БД.
    Використовується у Кроці 5 для побудови географічних карт.

    Args:
        df: сирий DataFrame з read_geolocation().

    Returns:
        DataFrame з колонками: zip_code | lat | lng
    """
    df = df.copy()

    df = df.rename(
        columns={
            "geolocation_zip_code_prefix": "zip_code",
            "geolocation_lat": "lat",
            "geolocation_lng": "lng",
        }
    )

    df = df.drop(columns=["geolocation_city", "geolocation_state"], errors="ignore")

    geo_agg = (
        df.groupby("zip_code")
        .agg(lat=("lat", "median"), lng=("lng", "median"))
        .reset_index()
    )

    print(f"  [geolocation] {len(df):,} → {len(geo_agg):,} рядків (унікальних zip)")
    return geo_agg
