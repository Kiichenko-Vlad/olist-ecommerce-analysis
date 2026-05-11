/*
Project: Olist E-Commerce Analysis
Query: Top 10 Product Categories by Revenue
Author: Vlad Kiichenko

Purpose:
Identify the highest-revenue product categories and their logistics cost ratio
to guide sourcing and marketing investment decisions.
Distinguishes high-margin "light" categories from heavy-logistics ones
by showing freight as a percentage of product revenue.
*/

-- Business Question:
-- Which 10 product categories generate the most revenue, and how does freight cost affect their margins?

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

-- Notes:
-- Revenue = SUM(price) without freight, per PM request (product revenue only)
-- freight_pct_of_revenue is an additional margin indicator:
--   high % = heavier logistics burden (e.g. bed_bath_table ~20%, watches_gifts ~8%)
-- DENSE_RANK handles potential revenue ties correctly
-- category = 'unknown' excluded (products without valid classification)
