/*
Project: Olist E-Commerce Analysis
Query: Revenue Geography — GMV by State
Author: Vlad Kiichenko

Purpose:
Map revenue concentration across Brazilian states and identify the relationship
between order volume and average order value to surface high-potential markets
where logistics barriers may be suppressing demand.
*/

-- Business Question:
-- Which states generate the most GMV, and where is there untapped revenue potential?

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

-- Notes:
-- GMV = SUM(price) without freight_value (product revenue only; consistent with Q2)
-- avg_order_value reveals an inverse pattern:
--   low-volume peripheral states have higher avg spend than SP
--   (e.g. PB: R$216.34, AP: R$198.15 vs SP: R$125.57 — difference of +73%)
-- SP generates ~40% of total GMV; top 3 states (SP, RJ, MG) account for ~66%
-- Northern states (RR, AP, AM) rank last in GMV but exceed SP in avg_order_value:
--   low volume is explained by logistics barriers, not by lack of demand or purchasing power
-- canceled / unavailable orders excluded for consistency with Q2 and Q5
