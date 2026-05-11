/*
Project: Olist E-Commerce Analysis
Query: Review Score Distribution (1–5 Stars)
Author: Vlad Kiichenko

Purpose:
Measure overall customer satisfaction and identify the share of negative reviews
to benchmark platform health and prioritize areas for service improvement.
*/

-- Business Question:
-- What is the distribution of review scores, and what share of reviews are negative (1–2 stars)?

SELECT
	score,
	COUNT(*) AS reviews_count,
	ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS share_pct,
	ROUND(SUM(COUNT(*)) OVER (ORDER BY score)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS cumulative_pct
FROM order_reviews
GROUP BY score
ORDER BY score;

-- Notes:
-- share_pct uses SUM(COUNT(*)) OVER () — window function applied over the aggregated result
-- cumulative_pct uses an ordered window to show running total by score
-- U-shape pattern observed: 1★ is 3.6× more common than 2★ (11,282 vs 3,114)
-- 14.62% negative reviews (1–2 stars) — above industry benchmark (~10%)
-- Selection bias applies: dissatisfied customers are more likely to leave reviews;
--   actual % of unhappy customers across all orders is likely lower than 14.62%
