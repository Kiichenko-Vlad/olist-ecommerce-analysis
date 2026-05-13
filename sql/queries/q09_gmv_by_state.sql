/*
Проєкт: Olist E-Commerce Analysis
Запит: Географія виручки — GMV по штатах
Автор: Vlad Kiichenko

Призначення:
Відобразити концентрацію виручки по штатах Бразилії та виявити зв'язок
між обсягом замовлень і середнім чеком — для визначення ринків з високим
потенціалом, де логістичні бар'єри стримують попит.
*/

-- Бізнес-питання:
-- Яка географія доходів платформи — які штати генерують найбільший GMV і яка середня цінність замовлення по регіонах?

SELECT
    DENSE_RANK() OVER (ORDER BY SUM(oi.price) DESC) AS revenue_rank,
    c.state,
    COUNT(DISTINCT o.order_id) AS orders_count,
    ROUND(SUM(oi.price)::numeric, 2) AS total_revenue,
    ROUND(SUM(oi.price)::numeric / COUNT(DISTINCT o.order_id), 2) AS avg_order_value
FROM customers AS c
JOIN orders AS o ON c.customer_id = o.customer_id
JOIN order_items AS oi ON oi.order_id = o.order_id
WHERE o.status NOT IN ('canceled', 'unavailable')
GROUP BY c.state
ORDER BY total_revenue DESC;

-- Примітки:
-- status NOT IN ('canceled', 'unavailable') замість = 'delivered': GMV включає відправлені та оброблювані замовлення як зафіксовану
--   виручку; узгоджено з визначенням обсягу в Q2 і Q5
-- COUNT(DISTINCT order_id): одне замовлення може містити кілька рядків order_items для одного штату; DISTINCT запобігає завищенню кількості
-- freight_value виключено з SUM: тільки дохід від товару, узгоджено з визначенням GMV у Q2
-- DENSE_RANK() розміщено безпосередньо в SELECT, а не в CTE: значення штату унікальні, збігів немає; однорівневий запит достатній
