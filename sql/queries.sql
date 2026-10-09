-- Expense Tracker SQL Queries
-- One query per use case

-- Use Case 1: As a user, I need to add a new expense category.
INSERT INTO categories (name) VALUES ('Travel');

-- Use Case 2: As a user, I need to view all categories.
SELECT id, name
FROM categories
ORDER BY name;

-- Use Case 3: As a user, I need to add a new expense.
-- Replace the values with actual input values at runtime.
INSERT INTO expenses (category_id, amount, description, date)
VALUES (1, 45.99, 'Grocery run', '2026-09-01');

-- Use Case 4: As a user, I need to view all expenses (most recent first).
SELECT e.id,
       c.name  AS category,
       e.amount,
       e.description,
       e.date
FROM expenses e
JOIN categories c ON e.category_id = c.id
ORDER BY e.date DESC;

-- Use Case 5: As a user, I need to view all expenses for a specific category.
-- Replace 'Food & Dining' with the desired category name.
SELECT e.id,
       e.amount,
       e.description,
       e.date
FROM expenses e
JOIN categories c ON e.category_id = c.id
WHERE c.name = 'Food & Dining'
ORDER BY e.date DESC;

-- Use Case 6: As a user, I need to view my total spending per category.
SELECT c.name        AS category,
       COUNT(e.id)   AS num_expenses,
       SUM(e.amount) AS total_spent
FROM categories c
LEFT JOIN expenses e ON c.id = e.category_id
GROUP BY c.id, c.name
ORDER BY total_spent DESC NULLS LAST;

-- Use Case 7: As a user, I need to view expenses within a date range.
-- Replace the date strings with the desired start and end dates.
SELECT e.id,
       c.name  AS category,
       e.amount,
       e.description,
       e.date
FROM expenses e
JOIN categories c ON e.category_id = c.id
WHERE e.date BETWEEN '2026-09-01' AND '2026-09-30'
ORDER BY e.date DESC;

-- Use Case 8: As a user, I need to view my total spending for a given month.
-- Replace '2026-09' with the desired year-month.
SELECT SUM(amount) AS monthly_total
FROM expenses
WHERE to_char(date, 'YYYY-MM') = '2026-09';

-- Use Case 9: As a user, I need to delete an expense.
-- Replace 1 with the id of the expense to delete.
DELETE FROM expenses WHERE id = 1;
