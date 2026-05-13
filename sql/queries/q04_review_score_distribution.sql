/*
Проєкт: Olist E-Commerce Analysis
Запит (Q4): Розподіл оцінок відгуків (1–5 зірок)
Автор: Vlad Kiichenko

Призначення:
Виміряти загальний рівень задоволеності клієнтів та визначити частку
негативних відгуків для оцінки стану платформи та пріоритизації
напрямків покращення сервісу.
*/

-- Бізнес-питання:
--  Як розподіляються оцінки відгуків і який % незадоволених клієнтів?

SELECT
	score,
	COUNT(*) AS reviews_count,
	ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS share_pct,
	ROUND(SUM(COUNT(*)) OVER (ORDER BY score)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS cumulative_pct
FROM order_reviews
GROUP BY score
ORDER BY score;

-- Примітки:
-- SUM(COUNT(*)) OVER(): віконна функція застосована до вже агрегованого результату — вимагає цього патерну подвійної агрегації в PostgreSQL
-- Приведення ::numeric обов'язкове перед ROUND: функція ROUND не приймає тип double precision безпосередньо в PostgreSQL
-- Впорядковане вікно в cumulative_pct використовує той самий OVER() фрейм, що й share_pct, але з ORDER BY для накопичення наростаючого підсумку