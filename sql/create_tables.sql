-- Таблиця клієнтів: кожен запис = інформація про одного клієнта.
-- Кожне замовлення має унікальний customer_id, навіть якщо один клієнт
-- робив кілька замовлень — це особливість анонімізації датасету.
CREATE TABLE customers (
    customer_id VARCHAR(32) PRIMARY KEY,
    customer_unique_id VARCHAR(32) NOT NULL,
    zip_code_prefix VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL
);
-- Таблиця продавців: кожен запис = інформація про одного продавця.
CREATE TABLE sellers (
    seller_id VARCHAR(32) PRIMARY KEY,
    zip_code_prefix VARCHAR(5) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(2) NOT NULL
);
-- Каталог товарів: кожен запис = один товар.
-- Колонки product_name_lenght, product_description_lenght з CSV
-- не включені, оскільки не використовуються в аналітичних запитах.
CREATE TABLE products (
    product_id VARCHAR(32) PRIMARY KEY,
    category_name_english VARCHAR(100) DEFAULT 'unknown',
    photos_qty SMALLINT CHECK (photos_qty >= 0),
    weight_g INT CHECK (weight_g > 0),
    length_cm INT CHECK (length_cm > 0),
    height_cm INT CHECK (height_cm > 0),
    width_cm INT CHECK (width_cm > 0)
);
-- Замовлення: кожен запис = одне замовлення клієнта.
CREATE TABLE orders (
    order_id VARCHAR(32) PRIMARY KEY,
    customer_id VARCHAR(32) REFERENCES customers(customer_id),
    status VARCHAR(15) NOT NULL,
    purchased_at TIMESTAMP NOT NULL,
    approved_at TIMESTAMP NULL,
    delivered_to_carrier_at TIMESTAMP NULL,
    delivered_to_customer_at TIMESTAMP NULL,
    estimated_delivery_at TIMESTAMP NULL
);
-- Позиції замовлень: кожен запис = один товар у замовленні.
-- Одне замовлення може містити кілька позицій (кілька рядків з однаковим order_id).
CREATE TABLE order_items (
    order_id VARCHAR(32) REFERENCES orders(order_id),
    order_item_id SMALLINT,
    product_id VARCHAR(32) REFERENCES products(product_id),
    seller_id VARCHAR(32) REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    freight_value DECIMAL(10, 2) NOT NULL DEFAULT 0 CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);
-- Платежі по замовленнях: кожен запис = одна платіжна транзакція.
-- Одне замовлення може мати кілька платежів (наприклад, частково ваучером, частково карткою).
CREATE TABLE order_payments (
    order_id VARCHAR(32) REFERENCES orders(order_id),
    payment_sequential SMALLINT NOT NULL,
    payment_type VARCHAR(15) NOT NULL,
    installments SMALLINT NOT NULL CHECK (installments >= 0),
    value DECIMAL(10, 2) NOT NULL CHECK (value >= 0),
    PRIMARY KEY (order_id, payment_sequential)
);
-- Відгуки клієнтів: кожен запис = один відгук після отримання замовлення.
CREATE TABLE order_reviews (
    review_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(32) REFERENCES orders(order_id),
    score SMALLINT NOT NULL CHECK (
        score BETWEEN 1 AND 5
    ),
    comment_title TEXT,
    comment_message TEXT,
    created_at TIMESTAMP NULL,
    answered_at TIMESTAMP NULL
);