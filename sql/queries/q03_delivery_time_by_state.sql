/*
Project: Olist E-Commerce Analysis
Query: Average Delivery Time by State with Stage Breakdown
Author: Vlad Kiichenko

Purpose:
Identify states with the longest delivery times and pinpoint whether delays
originate at the seller handling stage or the carrier transit stage.
Provides a data-driven basis for logistics partner negotiations
and warehouse placement decisions.
*/

-- Business Question:
-- Which states have the worst delivery performance, and is the bottleneck the seller or the carrier?

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

-- Notes:
-- Only 'delivered' orders with non-null delivered_to_carrier_at are included;
--   this ensures all three stage metrics share the same denominator (no NULL mismatch)
-- seller_handling_days  = purchased_at → delivered_to_carrier_at
-- carrier_transit_days  = delivered_to_carrier_at → delivered_to_customer_at
-- total_days            = purchased_at → delivered_to_customer_at
-- late_pct = % of orders delivered after estimated_delivery_at
-- avg_seller_handling is ~3–4 days across all 27 states: the bottleneck is the carrier, not sellers
-- States RR, AP, AC have small samples (41–80 orders); interpret results with caution
