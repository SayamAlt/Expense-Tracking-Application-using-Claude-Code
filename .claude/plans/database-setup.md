# Plan: Database Setup for Spendly

## Context

The Spendly expense tracker app currently has a stub `database/db.py` and a Flask `app.py` with placeholder routes. This task implements the SQLite data layer — `get_db()`, `init_db()`, and `seed_db()` — so all future features (auth, expenses) have a working database foundation.

---

## Step 1: Implement `database/db.py`

**File:** `database/db.py`

### `get_db()`
- Connect to `spendly.db` in the project root (use `os.path.join` relative to this file's directory)
- Set `connection.row_factory = sqlite3.Row`
- Execute `PRAGMA foreign_keys = ON`
- Return the connection

### `init_db()`
- Call `get_db()` to get a connection
- Execute `CREATE TABLE IF NOT EXISTS users` with columns:
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `name TEXT NOT NULL`
  - `email TEXT UNIQUE NOT NULL`
  - `password_hash TEXT NOT NULL`
  - `created_at TEXT DEFAULT (datetime('now'))`
- Execute `CREATE TABLE IF NOT EXISTS expenses` with columns:
  - `id INTEGER PRIMARY KEY AUTOINCREMENT`
  - `user_id INTEGER NOT NULL REFERENCES users(id)`
  - `amount REAL NOT NULL`
  - `category TEXT NOT NULL`
  - `date TEXT NOT NULL`
  - `description TEXT`
  - `created_at TEXT DEFAULT (datetime('now'))`
- Commit and close

### `seed_db()`
- Call `get_db()`, check `SELECT COUNT(*) FROM users` — if > 0, return early
- Insert demo user: name="Demo User", email="demo@spendly.com", password hashed via `werkzeug.security.generate_password_hash("demo123", method="pbkdf2:sha256")`
- Insert 8 expenses linked to the demo user covering all 7 categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other) + one duplicate category, with dates spread across the current month (use `datetime.date.today()` to derive YYYY-MM-DD dates)
- All inserts use parameterized queries (`?` placeholders)
- Commit and close

---

## Step 2: Update `app.py`

**File:** `app.py`

- Add import: `from database.db import get_db, init_db, seed_db`
- After `app = Flask(__name__)`, add:
  ```python
  with app.app_context():
      init_db()
      seed_db()
  ```
- No changes to existing routes

---

## Verification

1. **Run the app:** `python app.py` — should start without errors
2. **Check DB created:** `ls spendly.db` exists in project root
3. **Verify schema:** `sqlite3 spendly.db ".schema"` — both tables with correct columns/constraints
4. **Verify seed data:** `sqlite3 spendly.db "SELECT * FROM users;"` — 1 demo user with hashed password
5. **Verify expenses:** `sqlite3 spendly.db "SELECT * FROM expenses;"` — 8 rows across categories
6. **Idempotency:** Run `python app.py` again — no duplicate data
7. **Foreign keys:** `sqlite3 spendly.db "PRAGMA foreign_keys;"` returns 1; inserting expense with invalid user_id fails
