/*
Проєкт: Olist E-Commerce Analysis
Запит(Q2): Топ-10 категорій товарів за виручкою
Автор: Vlad Kiichenko

Призначення:
Визначити категорії з найвищою виручкою та їхнє співвідношення витрат
на логістику для прийняття рішень щодо пріоритизації асортименту
та маркетингових інвестицій.
Відрізняє "легкі" категорії з низькими логістичними витратами від
важких категорій з високою часткою фрахту у виручці.
*/

-- Бізнес-питання:
-- Які топ-10 категорій генерують найбільший дохід?

WITH total_category_price AS (
	SELECT
		p.category_name_english AS category_name,
		ROUND(SUM(oi.price), 2) AS total_revenue,
		ROUND(SUM(oi.freight_value), 2) AS total_freight,
		ROUND(SUM(oi.freight_value) / SUM(oi.price) * 100, 1) AS freight_pct_of_revenue
	FROM products AS p
	JOIN order_items AS oi
		ON p.product_id = oi.product_id
	JOIN orders AS o
		ON o.order_id = oi.order_id
	WHERE true
		AND p.category_name_english <> 'unknown'
		AND o.status = 'delivered'
	GROUP BY category_name
),
all_rank AS (
	SELECT
		category_name,
		total_revenue,
		total_freight,
		freight_pct_of_revenue,
		DENSE_RANK() OVER(ORDER BY total_revenue DESC) AS revenue_rank
	FROM total_category_price
)
select
	revenue_rank,
	category_name,
	total_revenue,
	total_freight,
	freight_pct_of_revenue
FROM all_rank
WHERE true
	AND revenue_rank <= 10
ORDER BY revenue_rank;

-- Примітки:
-- Фільтр status = 'delivered' через JOIN з orders: враховуються тільки завершені транзакції; виручка скасованих або відправлених
--   замовлень ще не реалізована
-- Категорія 'unknown' виключена: ці товари не отримали валідної класифікації під час ETL-трансформації і непридатні для групування
-- freight_value виключено з виручки: SUM(price) вимірює дохід від продажу товару; фрахт — транзитна вартість, а не дохід платформи
-- DENSE_RANK замість ROW_NUMBER: коректно обробляє збіги виручки без довільного пропуску рангів
