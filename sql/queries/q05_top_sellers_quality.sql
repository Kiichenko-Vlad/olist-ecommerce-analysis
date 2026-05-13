/*
Проєкт: Olist E-Commerce Analysis
Запит: Топ-10 продавців за обсягом замовлень з метриками якості
Автор: Vlad Kiichenko

Призначення:
Визначити найактивніших продавців та оцінити, чи корелює високий обсяг
замовлень з якістю сервісу. Використовує avg_score, critical_pct (частка
оцінок 1 зірка) та negative_pct (частка 1–2 зірки) для багатовимірної
оцінки якості.
*/

-- Бізнес-питання:
-- Хто топ-10 продавців за активністю і яка їхня середня оцінка?

WITH seller_orders AS  (	
	SELECT
		s.seller_id,
		s.city,
		s.state,
		o.order_id
	FROM sellers AS s
	JOIN order_items AS ot
		ON s.seller_id  = ot.seller_id 
	JOIN orders AS o
		ON ot.order_id = o.order_id
	WHERE true
		AND o.status NOT IN ('canceled', 'unavailable')
),
seller_metrics AS (
	SELECT
		so.seller_id,
		so.city,
		so.state,
		COUNT(DISTINCT so.order_id) AS total_orders,
		ROUND(AVG(orv.score), 2) AS avg_score,
		ROUND(
    		  AVG(CASE WHEN orv.score = 1 THEN 100.0 ELSE 0 END) 
        	  FILTER (WHERE orv.score IS NOT NULL), 2
        	  ) AS critical_pct,
		ROUND(
		      AVG(CASE WHEN orv.score <= 2 THEN 100.0 ELSE 0 END) 
		      FILTER (WHERE orv.score IS NOT NULL), 2
		      ) AS negative_pct
	FROM seller_orders AS so
	LEFT JOIN order_reviews AS orv
		ON so.order_id = orv.order_id
	GROUP BY so.seller_id, so.city, so.state
),
ranked AS (
    SELECT *,
           DENSE_RANK() OVER (ORDER BY total_orders DESC) AS seller_rank
    FROM seller_metrics
)
SELECT 
	seller_rank, 
	seller_id, 
	city, 
	state, 
	total_orders, 
	avg_score,
	critical_pct,
	negative_pct
FROM ranked
WHERE seller_rank <= 10
ORDER BY seller_rank;

-- Примітки:
-- LEFT JOIN order_reviews: продавці без відгуків мають залишатися у результаті; INNER JOIN мовчки виключив би їх із рейтингу
-- FILTER (WHERE score IS NOT NULL): критично важливий захист коректності — без нього NULL з LEFT JOIN давали б 0 через CASE WHEN і занижували б
--   critical_pct / negative_pct за рахунок замовлень без відгуків
-- 100.0 у CASE WHEN примушує до ділення з плаваючою точкою; ціле число 1 у деяких крайніх випадках дало б 0 після AVG
-- COUNT(DISTINCT order_id): одне замовлення може містити кілька позицій від одного продавця через order_items; DISTINCT запобігає завищенню
-- status NOT IN ('canceled', 'unavailable'): активність продавця включає відправлені та оброблювані замовлення, не лише доставлені
