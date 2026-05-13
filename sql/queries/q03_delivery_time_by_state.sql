/*
Проєкт: Olist E-Commerce Analysis
Запит(Q3): Середній час доставки по штатах з розбивкою за етапами
Автор: Vlad Kiichenko

Призначення:
Визначити штати з найдовшим часом доставки та з'ясувати, де виникає
затримка — на етапі обробки замовлення продавцем чи під час транзиту
перевізника. Надає аналітичну основу для переговорів з логістичними
партнерами та рішень щодо розміщення складів.
*/

-- Бізнес-питання:
-- Який середній час доставки по штатах і де найгірша логістика?

WITH delivered_orders AS (
	SELECT
		o.order_id,
		o.customer_id,
		EXTRACT(EPOCH FROM (o.delivered_to_carrier_at - o.purchased_at)) / 86400 AS seller_handling_days,
		EXTRACT(EPOCH FROM (o.delivered_to_customer_at - o.delivered_to_carrier_at)) / 86400 AS carrier_transit_days,
		EXTRACT(EPOCH FROM (o.delivered_to_customer_at - o.purchased_at)) / 86400 AS total_days,
		CASE 
			WHEN o.delivered_to_customer_at > o.estimated_delivery_at THEN 1 
			ELSE 0 
		END AS is_late
	FROM orders AS o
	WHERE true
		AND o.status = 'delivered'
	  	AND o.delivered_to_customer_at IS NOT NULL
	  	AND o.delivered_to_customer_at >= o.purchased_at
	  	AND o.delivered_to_carrier_at IS NOT NULL
),
state_metrics AS (
	SELECT
		c.state AS state,
		COUNT(dor.order_id) AS orders,
		ROUND(AVG(seller_handling_days)::numeric, 2) AS avg_seller_handling_days,
		ROUND(AVG(carrier_transit_days)::numeric, 2) AS avg_carrier_transit_days,
		ROUND(AVG(total_days)::numeric, 2) AS avg_total_days,
		ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_days)::numeric, 2) AS median_total,
		ROUND((AVG(is_late) * 100)::numeric, 2) AS late_pct
	FROM customers AS c
	JOIN delivered_orders AS dor
		ON c.customer_id = dor.customer_id
	GROUP BY state
)
SELECT
	DENSE_RANK() OVER(ORDER BY avg_total_days DESC) AS delivered_days_rank,
	state,
	orders,
	avg_seller_handling_days,
	avg_carrier_transit_days,
	avg_total_days,
	median_total,
	late_pct
FROM state_metrics;

-- Примітки:
-- Умова delivered_to_carrier_at IS NOT NULL обов'язкова на додаток до delivered_to_customer_at: забезпечує однаковий знаменник для всіх
--   трьох метрик (seller_handling, carrier_transit, total); без неї розбивка по етапах неможлива
-- Умова delivered_to_customer_at >= purchased_at захищає від аномалій даних, де дата доставки передує даті замовлення (логічна неможливість)
-- EXTRACT(EPOCH FROM interval) / 86400: PostgreSQL-специфічна конвертація інтервалу у дробові дні (секунди → дні)
-- PERCENTILE_CONT(0.5): медіана стійкіша за AVG для скошених розподілів часу доставки з викидами
