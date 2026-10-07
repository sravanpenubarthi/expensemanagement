-- SQLite schema for the Expense Management API
-- (tables are also created automatically by SQLAlchemy on startup)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS expenses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name  VARCHAR(100) NOT NULL,
    category_id    INTEGER NOT NULL,
    amount         REAL NOT NULL CHECK (amount > 0),
    description    VARCHAR(255) NOT NULL,
    expense_date   DATE NOT NULL,
    payment_method VARCHAR(20) NOT NULL
        CHECK (payment_method IN ('Cash', 'Card', 'UPI', 'Bank Transfer')),
    status         VARCHAR(20) NOT NULL DEFAULT 'Pending'
        CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    created_date   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE INDEX IF NOT EXISTS ix_expenses_category_id ON expenses (category_id);
CREATE INDEX IF NOT EXISTS ix_expenses_expense_date ON expenses (expense_date);
