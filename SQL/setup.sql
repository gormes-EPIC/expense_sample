-- Expense Tracker Database Setup
-- Creates the categories and expenses tables

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id INTEGER        NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
    description TEXT           NOT NULL,
    date        DATE           NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Seed default categories
INSERT INTO categories (name) VALUES
    ('Food & Dining'),
    ('Transportation'),
    ('Housing'),
    ('Entertainment'),
    ('Health & Medical'),
    ('Shopping'),
    ('Utilities'),
    ('Other')
ON CONFLICT (name) DO NOTHING;
