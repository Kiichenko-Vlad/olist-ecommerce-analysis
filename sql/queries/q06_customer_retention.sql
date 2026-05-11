/*
Project: Olist E-Commerce Analysis
Query: Customer Retention Analysis
Author: Vlad Kiichenko

Purpose:
Measure the share of customers who made repeat purchases to assess platform loyalty,
quantify the retention gap, and provide a segmented view of customer engagement depth
as a key KPI for executive reporting.
*/

-- Business Question:
-- What percentage of customers made more than one purchase (retention rate)?

WITH order_customer AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS orders_count
    FROM customers AS c
        JOIN orders AS o ON c.customer_id = o.customer_id
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

-- Notes:
-- Uses customer_unique_id, NOT customer_id: in Olist each order receives a new customer_id,
--   so customer_unique_id is the correct identifier for repeat-purchase analysis
-- No order status filter: even canceled repeat orders indicate purchase intent
-- Result: retention_pct ~3.12%, avg_orders = 1.03
-- Low retention is expected for a non-grocery marketplace with durable goods
--   (furniture, watches, sports) that are bought infrequently by nature
-- Dataset cutoff (2016–2018) may artificially lower retention:
--   customers from late 2018 had less time to make a second purchase
