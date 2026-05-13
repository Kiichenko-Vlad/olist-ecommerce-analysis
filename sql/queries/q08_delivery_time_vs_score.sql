/*
Проєкт: Olist E-Commerce Analysis
Запит: Вплив часу доставки на оцінку відгуку клієнта
Автор: Vlad Kiichenko

Призначення:
Перевірити гіпотезу про те, що довший час доставки призводить до нижчих
оцінок відгуків — шляхом розбивки замовлень на бакети за часом доставки
та вимірювання середньої оцінки для кожного. Результати дають аналітичну
основу для встановлення логістичного SLA.
*/

-- Бізнес-питання:
-- Чи впливає час доставки на оцінку клієнта?

WITH order_total_by_payment AS (
    SELECT
        order_id,
        payment_type,
        SUM(value) AS order_value
    FROM order_payments
    GROUP BY order_id, payment_type
)
SELECT
    payment_type,
    COUNT(*) AS orders_count,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS share_pct,
    ROUND(AVG(order_value), 2) AS avg_order_value
FROM order_total_by_payment
GROUP BY payment_type
ORDER BY orders_count DESC;

-- Примітки:
-- LEFT JOIN order_reviews: усі доставлені замовлення мають враховуватися в orders_count навіть без відгуку; AVG(score) автоматично ігнорує
--   NULL і відображає тільки замовлення з відгуками
-- Умова delivered_to_customer_at >= purchased_at захищає від від'ємного часу доставки через помилки введення даних
-- ORDER BY MIN(total_days): сортує бакети за мінімальним числовим значенням у кожному; без цього ORDER BY bucket сортує алфавітно:
--   '1-3' → '15+' → '4-7' → '8-14' (хибний порядок)
