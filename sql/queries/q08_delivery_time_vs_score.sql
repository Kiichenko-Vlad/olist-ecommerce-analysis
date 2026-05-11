/*
Project: Olist E-Commerce Analysis
Query: Delivery Time Impact on Customer Review Score
Author: Vlad Kiichenko

Purpose:
Test the hypothesis that longer delivery times lead to lower review scores by
bucketing orders into delivery time ranges and measuring average score per bucket.
Results provide a data-driven basis for setting a logistics SLA.
*/

-- Business Question:
-- Does delivery time affect customer satisfaction, and where is the critical performance threshold?

WITH delivered_orders AS (
	SELECT
		o.order_id,
		o.customer_id,
		ROUND(EXTRACT(EPOCH FROM (o.delivered_to_customer_at - o.purchased_at))::numeric / 86400, 2) AS total_days
	FROM orders AS o
	WHERE true
		AND o.status = 'delivered'
	  	AND o.delivered_to_customer_at IS NOT NULL
	  	AND o.delivered_to_customer_at >= o.purchased_at
)
SELECT
	CASE
		WHEN dor.total_days < 4 THEN '1-3'
		WHEN dor.total_days < 8 THEN '4-7'
		WHEN dor.total_days < 15 THEN '8-14'
		ELSE '15+'
	END AS bucket,
	COUNT(dor.order_id) AS orders_count,
	ROUND(AVG(orv.score), 2) AS avg_score
FROM delivered_orders AS dor
LEFT JOIN order_reviews AS orv
	ON dor.order_id = orv.order_id
GROUP BY bucket
ORDER BY MIN(dor.total_days);

-- Notes:
-- LEFT JOIN retains all delivered orders in the count (incl. those without a review)
-- avg_score computed only for orders with reviews (AVG ignores NULL values)
-- 27.4% of orders fall in the 15+ bucket — not a marginal edge case
-- Key finding: threshold effect at 15 days
--   Score drops -0.64 at 15+ vs 8–14 days (4.29 → 3.65) — 6× larger than earlier bucket drops
-- Recommended SLA: max 14 days keeps avg_score ≥ 4.29
-- Northern states (RR, AP, AM) average 26–29 days → almost all fall in the critical bucket
