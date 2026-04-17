import sqlite3
import os
import random
from datetime import datetime, timedelta
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "spendly.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def seed_expenses(user_id, count, months):
    # Verify user exists
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        conn.close()
        print(f"No user found with id {user_id}.")
        return

    # Define categories with realistic Canadian descriptions and amounts (CAD)
    categories = [
        {
            "name": "Food",
            "amount_range": (50, 800),
            "descriptions": ["Grocery shopping", "Restaurant dinner", "Coffee run", "Lunch at work",
                           "Snacks", "Takeout", "Meal kit", "Produce shopping", "Bakery items"],
            "weight": 0.3  # 30% of expenses
        },
        {
            "name": "Transport",
            "amount_range": (20, 500),
            "descriptions": ["Bus pass", "Gas refill", "Taxi ride", "Parking fee", "Uber ride",
                           "Train ticket", "Car maintenance", "Bike repair", "Fuel"],
            "weight": 0.2  # 20% of expenses
        },
        {
            "name": "Bills",
            "amount_range": (200, 3000),
            "descriptions": ["Electricity bill", "Internet bill", "Phone bill", "Rent",
                           "Insurance", "Water bill", "Cable TV", "Hydro bill", "Mortgage"],
            "weight": 0.2  # 20% of expenses
        },
        {
            "name": "Health",
            "amount_range": (100, 2000),
            "descriptions": ["Pharmacy", "Doctor visit", "Dental checkup", "Prescription",
                           "Health insurance", "Vitamins", "Medical test", "Dental cleaning"],
            "weight": 0.1  # 10% of expenses
        },
        {
            "name": "Entertainment",
            "amount_range": (100, 1500),
            "descriptions": ["Movie tickets", "Concert tickets", "Streaming service",
                           "Video game", "Books", "Netflix", "Spotify", "Theater show"],
            "weight": 0.1  # 10% of expenses
        },
        {
            "name": "Shopping",
            "amount_range": (200, 5000),
            "descriptions": ["Clothing", "Electronics", "Home goods", "Shoes", "Jewelry",
                           "Furniture", "Appliances", "Toys", "Kitchenware"],
            "weight": 0.05  # 5% of expenses
        },
        {
            "name": "Other",
            "amount_range": (50, 1000),
            "descriptions": ["Gift for friend", "Donation", "Subscription", "Repair service",
                           "Office supplies", "School supplies", "Pet supplies", "Miscellaneous"],
            "weight": 0.05  # 5% of expenses
        }
    ]

    # Calculate weights for random selection
    total_weight = sum(cat["weight"] for cat in categories)
    normalized_weights = [cat["weight"] / total_weight for cat in categories]

    # Generate random dates across the past <months> months
    today = datetime.now()
    start_date = today - timedelta(days=months * 30)

    # Generate expenses
    expenses = []
    for _ in range(count):
        # Select category based on weights
        category = random.choices(categories, weights=normalized_weights)[0]

        # Generate random amount
        amount = random.randint(*category["amount_range"]) + random.random()

        # Generate random date
        random_days = random.randint(0, (today - start_date).days)
        expense_date = today - timedelta(days=random_days)

        # Select random description
        description = random.choice(category["descriptions"])

        expenses.append((
            user_id,
            round(amount, 2),
            category["name"],
            expense_date.strftime("%Y-%m-%d"),
            description
        ))

    # Insert all expenses in a single transaction
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        conn.commit()

        # Get the inserted records for confirmation
        cursor.execute("""
            SELECT date, amount, category, description
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 5
        """, (user_id,))
        sample_records = cursor.fetchall()

        # Calculate date range
        min_date = min(expense[3] for expense in expenses)
        max_date = max(expense[3] for expense in expenses)

        print(f"Successfully inserted {count} expenses for user {user_id}")
        print(f"Date range: {min_date} to {max_date}")
        print("\nSample of 5 inserted records:")
        print("-" * 80)
        for record in sample_records:
            print(f"{record['date']} | ${record['amount']:8.2f} | {record['category']:12} | {record['description']}")

        conn.close()
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"Error inserting expenses: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python seed_expenses.py <user_id> <count> <months>")
        print("Example: python seed_expenses.py 1 50 6")
        sys.exit(1)

    user_id = int(sys.argv[1])
    count = int(sys.argv[2])
    months = int(sys.argv[3])

    seed_expenses(user_id, count, months)