/*
Project: Olist E-Commerce Analysis
Query: Payment Method Distribution and Average Order Value
Author: Vlad Kiichenko

Purpose:
Analyze how customers are distributed across payment methods and whether
payment type correlates with order value, to inform checkout UX design
and payment partnership strategy.
*/

-- Business Question:
-- How are payment methods distributed, and does payment type influence average order value?

WITH order_total_by_payment AS (
    SELECT
        order_id,
        payment_type,
        SUM(value) AS order_value
    FROM order_payments
    GROUP BY order_id, payment_type
)
SELECT
    payment_type,
    COUNT(*) AS orders_count,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS share_pct,
    ROUND(AVG(order_value), 2) AS avg_order_value
FROM order_total_by_payment
GROUP BY payment_type
ORDER BY orders_count DESC;

-- Notes:
-- Aggregated at (order_id, payment_type) level to avoid double-counting installment rows
-- Total records (~102k) > total orders (~99k): some orders use multiple payment methods
-- credit_card: 75.24% — driven by Brazilian parcelamento (interest-free installments up to 12 months)
-- boleto: 19.46% — bank slip for customers without credit cards; critical channel to retain
-- avg_order_value for credit_card (R$163.94) and boleto (R$145.03) differ by only 13%:
--   payment type does NOT correlate with order size — they represent distinct audience segments
-- voucher avg is low (R$98.15) because it is typically used as partial payment alongside credit_card
-- 3 records with payment_type = 'not_defined' (value = 0) are a data anomaly; negligible impact
