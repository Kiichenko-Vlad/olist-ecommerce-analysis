/*
Project: Olist E-Commerce Analysis
Query: Monthly Order Volume Dynamics (2016–2018)
Author: Vlad Kiichenko

Purpose:
Track month-over-month order volume to assess platform growth trajectory
and identify seasonal patterns (e.g. Black Friday) for investor presentations
and operational capacity planning.
*/

-- Business Question:
-- How has the order volume grown over time, and are there seasonal peaks?

SELECT
    TO_CHAR(DATE_TRUNC('month', o.purchased_at), 'YYYY-MM') AS period,
    COUNT(*) AS order_count
FROM orders AS o
GROUP BY period
ORDER BY period ASC;

-- Notes:
-- All order statuses included (incl. canceled) to reflect full platform activity
-- Data for Sep–Dec 2016 and Aug–Oct 2018 is incomplete due to dataset cutoff;
--   low values at period edges are data artifacts, not real business decline
-- Nov 2017 spike expected: Black Friday in Brazil is the largest annual shopping peak
