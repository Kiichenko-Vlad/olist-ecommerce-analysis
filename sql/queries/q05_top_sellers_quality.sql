/*
Project: Olist E-Commerce Analysis
Query: Top 10 Sellers by Order Volume with Quality Metrics
Author: Vlad Kiichenko

Purpose:
Identify the most active sellers and evaluate whether high order volume
correlates with service quality. Uses avg_score, critical_pct (1-star share),
and negative_pct (1–2 star share) for a multi-dimensional quality view.
*/

-- Business Question:
-- Who are the top 10 most active sellers, and do high-volume sellers maintain service quality?

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

-- Notes:
-- LEFT JOIN order_reviews retains sellers with no reviews (their avg_score will be NULL)
-- critical_pct  = % of 1-star reviews only — most severe dissatisfaction signal
-- negative_pct  = % of 1–2 star reviews — broader dissatisfaction indicator
-- FILTER (WHERE score IS NOT NULL) excludes unreviewed orders from percentage calculations;
--   without it, LEFT JOIN NULLs would resolve to 0 via CASE WHEN and dilute critical_pct / negative_pct
-- All top 10 sellers are in SP state — significant geographic concentration risk
-- Volume–quality correlation is weak: critical_pct ranges 7.74%–14.73% among top 10
