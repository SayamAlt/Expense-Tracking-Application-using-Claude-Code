import sqlite3
import os
from collections import Counter
from datetime import date
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "spendly.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_expenses_for_user(conn, user_id, start_date=None, end_date=None):
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date DESC"
    return conn.execute(query, params).fetchall()


def summarise_expenses(expenses):
    total_spent = sum(float(e["amount"]) for e in expenses)
    average = total_spent / len(expenses) if expenses else 0
    category_totals = Counter()
    for e in expenses:
        category_totals[e["category"]] += float(e["amount"])
    top_category = category_totals.most_common(1)[0] if category_totals else ("None", 0)
    total_for_percent = total_spent if total_spent > 0 else 1
    category_breakdown = [
        {
            "name": cat,
            "amount": amt,
            "percentage": round((amt / total_for_percent) * 100, 1),
        }
        for cat, amt in category_totals.most_common()
    ]
    return total_spent, average, top_category, category_breakdown


def seed_db():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123", method="pbkdf2:sha256")
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )

    today = date.today()
    expenses = [
        (1, 45.50, "Food", today.replace(day=1).isoformat(), "Grocery shopping"),
        (1, 12.00, "Transport", today.replace(day=3).isoformat(), "Bus pass top-up"),
        (1, 120.00, "Bills", today.replace(day=5).isoformat(), "Electricity bill"),
        (1, 35.00, "Health", today.replace(day=8).isoformat(), "Pharmacy"),
        (1, 25.00, "Entertainment", today.replace(day=10).isoformat(), "Movie tickets"),
        (1, 89.99, "Shopping", today.replace(day=12).isoformat(), "New headphones"),
        (1, 15.00, "Other", today.replace(day=15).isoformat(), "Gift for friend"),
        (1, 32.75, "Food", today.replace(day=18).isoformat(), "Restaurant dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )

    conn.commit()
    conn.close()
