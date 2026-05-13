/*
Проєкт: Olist E-Commerce Analysis
Запит: Розподіл способів оплати та середній чек
Автор: Vlad Kiichenko

Призначення:
Проаналізувати розподіл клієнтів за способами оплати та з'ясувати,
чи корелює тип оплати із середнім чеком — для прийняття рішень щодо
UX оплати та стратегії платіжного партнерства.
*/

-- Бізнес-питання:
-- Який середній чек по кожному типу оплати?

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
-- CTE агрегує на рівні (order_id, payment_type) до основного SELECT: без цього рядки розстрочок (один рядок на кожен внесок) завищують
--   orders_count і спотворюють avg_order_value
-- Загальна кількість записів у CTE (~102k) > замовлень (~99k): очікувано — замовлення з кількома способами оплати дають кілька рядків на order_id
-- 3 записи з payment_type = 'not_defined' і value = 0 — аномалія вихідних даних; включені для повноти, вплив на аналіз незначний