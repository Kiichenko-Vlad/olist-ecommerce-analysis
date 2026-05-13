/*
Проєкт: Olist E-Commerce Analysis
Запит: Аналіз утримання клієнтів (Retention Analysis)
Автор: Vlad Kiichenko

Призначення:
Виміряти частку клієнтів, які здійснили повторні покупки, для оцінки
лояльності платформи та сегментованого погляду на глибину залученості
клієнтів як ключового KPI для управлінської звітності.
*/

-- Бізнес-питання:
-- Яка частка клієнтів повертається для повторної покупки?

WITH order_customer AS (	
	SELECT
		c.customer_unique_id,
		COUNT(DISTINCT o.order_id) AS orders_count
	FROM customers AS c
	JOIN orders AS o
		ON c.customer_id = o.customer_id
	GROUP BY c.customer_unique_id
)
SELECT
	COUNT(*) AS total_customers,
	COUNT(*) FILTER (WHERE orders_count = 1) AS one_time_customers,
	COUNT(*) FILTER (WHERE orders_count >= 2) AS repeat_customers,
    COUNT(*) FILTER (WHERE orders_count >= 3) AS frequent_customers,
    COUNT(*) FILTER (WHERE orders_count >= 4) AS loyal_customers,
	COUNT(*) FILTER (WHERE orders_count >= 5) AS power_users_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE orders_count >= 2) / COUNT(*), 2) AS retention_pct,
    ROUND(AVG(orders_count), 2) AS avg_orders_per_customer,
    MAX(orders_count) AS max_orders_per_customer
FROM order_customer;

-- Примітки:
-- customer_unique_id, а НЕ customer_id: Olist присвоює новий customer_id кожному замовленню; підрахунок по customer_id зробив би кожного
--   клієнта одноразовим покупцем незалежно від реальних повторних покупок
-- Фільтр по статусу відсутній: скасоване повторне замовлення все одно свідчить про намір купити і не має виключатися з воронки лояльності
-- Сегменти є кумулятивними підмножинами один одного: repeat (≥2) ⊃ frequent (≥3) ⊃ loyal (≥4) ⊃ power_users (≥5)
-- COUNT(*) FILTER (WHERE ...): однопрохідна альтернатива кільком підзапитам або патерну CASE WHEN SUM
