# Tests for Step 07: Add Expense Feature
#
# Spec behaviors verified:
#   - GET /expenses/add while logged out redirects to /login (auth guard)
#   - POST /expenses/add while logged out redirects to /login (auth guard)
#   - GET /expenses/add while logged in returns 200 and renders the form
#   - GET /expenses/add populates the date field with today's date in YYYY-MM-DD format
#   - GET /expenses/add renders all seven predefined category options
#   - POST with valid data inserts one expense row in the DB and redirects to /profile
#   - POST with valid data flashes a success message after redirect
#   - POST with valid data stores correct field values in the DB
#   - POST with missing amount re-renders the form (no redirect) with an error message
#   - POST with zero amount re-renders the form with a validation error
#   - POST with a negative amount re-renders the form with a validation error
#   - POST with a non-numeric amount string re-renders the form with a validation error
#   - POST with missing category re-renders the form with a validation error
#   - POST with a category not in the allowed list re-renders the form with a validation error
#   - POST with missing date re-renders the form with a validation error
#   - POST validation failures do NOT insert any row in the DB
#   - After a validation error the submitted amount value is preserved in the form
#   - After a validation error the submitted category value is preserved in the form
#   - After a validation error the submitted date value is preserved in the form
#   - After a validation error the submitted description value is preserved in the form
#   - The profile page contains a link/button navigating to /expenses/add

import pytest
import sqlite3
import tempfile
import os
from datetime import date
from unittest.mock import patch, MagicMock

from app import app
from database import db as db_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALLOWED_CATEGORIES = ["Food", "Transport", "Bills", "Health",
                       "Entertainment", "Shopping", "Other"]


def _make_db(path):
    """Create a fully initialised SQLite database at *path* and return it."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
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
    return conn


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path):
    """
    Yields a Flask test client backed by a fresh temporary SQLite database.

    Every test gets its own isolated database file so there is no shared state.
    The patch replaces database.db.get_db (and the reference imported into
    app.py) with a factory that always connects to the temp file.
    """
    db_file = str(tmp_path / "test_spendly.db")

    # Pre-create the schema so the factory connection is ready immediately.
    seed_conn = _make_db(db_file)
    seed_conn.close()

    def _get_test_db():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    with patch.object(db_module, "get_db", side_effect=_get_test_db), \
         patch("app.get_db", side_effect=_get_test_db):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        with app.test_client() as test_client:
            yield test_client, db_file


def _register_and_login(test_client, db_file,
                        name="Alice", email="alice@example.com",
                        password="password123"):
    """
    Insert a user directly into the DB and set the session so the test client
    is authenticated.  Returns the user_id.
    """
    from werkzeug.security import generate_password_hash
    pw_hash = generate_password_hash(password, method="pbkdf2:sha256")
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, pw_hash),
    )
    conn.commit()
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()["id"]
    conn.close()

    # Use the login route to obtain a proper session cookie.
    test_client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    return user_id


def _expense_count(db_file, user_id):
    """Return the number of expense rows for *user_id* in the temp DB."""
    conn = sqlite3.connect(db_file)
    count = conn.execute(
        "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    conn.close()
    return count


def _fetch_expenses(db_file, user_id):
    """Return all expense rows for *user_id* as sqlite3.Row objects."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC", (user_id,)
    ).fetchall()
    conn.close()
    return rows


# ---------------------------------------------------------------------------
# Auth guard tests
# ---------------------------------------------------------------------------

class TestAddExpenseAuthGuard:

    def test_get_add_expense_while_logged_out_redirects_to_login(self, client):
        test_client, _ = client
        response = test_client.get("/expenses/add", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_get_add_expense_logged_out_eventually_lands_on_login_page(self, client):
        test_client, _ = client
        response = test_client.get("/expenses/add", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower() or b"log in" in response.data.lower()

    def test_post_add_expense_while_logged_out_redirects_to_login(self, client):
        test_client, _ = client
        response = test_client.post(
            "/expenses/add",
            data={
                "amount": "100",
                "category": "Food",
                "date": "2026-04-30",
                "description": "test",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_add_expense_logged_out_does_not_insert_row(self, client):
        test_client, db_file = client
        # Insert a user so we can count their expenses (none should appear).
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash("pw123456", method="pbkdf2:sha256")
        conn = sqlite3.connect(db_file)
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Bob", "bob@example.com", pw_hash),
        )
        conn.commit()
        uid = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("bob@example.com",)
        ).fetchone()[0]
        conn.close()

        test_client.post(
            "/expenses/add",
            data={"amount": "100", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, uid) == 0


# ---------------------------------------------------------------------------
# GET /expenses/add — happy path
# ---------------------------------------------------------------------------

class TestGetAddExpenseForm:

    def test_get_returns_200_when_authenticated(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert response.status_code == 200

    def test_get_renders_amount_input(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert b'name="amount"' in response.data

    def test_get_renders_category_select(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert b'name="category"' in response.data

    def test_get_renders_date_input(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert b'name="date"' in response.data

    def test_get_renders_description_textarea(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert b'name="description"' in response.data

    def test_get_date_field_defaults_to_today(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        today_iso = date.today().isoformat()
        assert today_iso.encode() in response.data

    def test_get_renders_all_seven_category_options(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        html = response.data
        for cat in ALLOWED_CATEGORIES:
            assert cat.encode() in html, f"Category '{cat}' not found in form"

    def test_get_renders_submit_button(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        # The spec requires an "Add Expense" submit button.
        assert b"Add Expense" in response.data

    def test_get_renders_cancel_link_to_profile(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/expenses/add")
        assert b"/profile" in response.data


# ---------------------------------------------------------------------------
# POST /expenses/add — happy path
# ---------------------------------------------------------------------------

class TestPostAddExpenseHappyPath:

    def test_valid_submission_redirects_to_profile(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={
                "amount": "250.50",
                "category": "Food",
                "date": "2026-04-15",
                "description": "Weekly groceries",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]

    def test_valid_submission_inserts_one_row_in_db(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "75.00",
                "category": "Transport",
                "date": "2026-04-20",
                "description": "Taxi",
            },
        )
        assert _expense_count(db_file, user_id) == 1

    def test_valid_submission_stores_correct_amount(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "123.45",
                "category": "Bills",
                "date": "2026-04-10",
                "description": "",
            },
        )
        rows = _fetch_expenses(db_file, user_id)
        assert len(rows) == 1
        assert float(rows[0]["amount"]) == pytest.approx(123.45)

    def test_valid_submission_stores_correct_category(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "50",
                "category": "Health",
                "date": "2026-04-10",
                "description": "Vitamins",
            },
        )
        rows = _fetch_expenses(db_file, user_id)
        assert rows[0]["category"] == "Health"

    def test_valid_submission_stores_correct_date(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "30",
                "category": "Entertainment",
                "date": "2026-03-22",
                "description": "",
            },
        )
        rows = _fetch_expenses(db_file, user_id)
        assert rows[0]["date"] == "2026-03-22"

    def test_valid_submission_stores_correct_description(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "20",
                "category": "Other",
                "date": "2026-04-01",
                "description": "A unique description string",
            },
        )
        rows = _fetch_expenses(db_file, user_id)
        assert rows[0]["description"] == "A unique description string"

    def test_valid_submission_stores_correct_user_id(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "99",
                "category": "Shopping",
                "date": "2026-04-28",
                "description": "",
            },
        )
        rows = _fetch_expenses(db_file, user_id)
        assert rows[0]["user_id"] == user_id

    def test_valid_submission_flashes_success_message(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={
                "amount": "10",
                "category": "Food",
                "date": "2026-04-30",
                "description": "",
            },
            follow_redirects=True,
        )
        assert b"success" in response.data.lower() or b"added" in response.data.lower()

    def test_valid_submission_with_optional_description_empty(self, client):
        """Description is optional; an empty description must still be accepted."""
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={
                "amount": "5.00",
                "category": "Other",
                "date": "2026-04-30",
                "description": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert _expense_count(db_file, user_id) == 1

    def test_multiple_submissions_insert_multiple_rows(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        for i in range(3):
            test_client.post(
                "/expenses/add",
                data={
                    "amount": str(10 + i),
                    "category": "Food",
                    "date": "2026-04-30",
                    "description": f"item {i}",
                },
            )
        assert _expense_count(db_file, user_id) == 3


# ---------------------------------------------------------------------------
# POST /expenses/add — validation: missing / invalid amount
# ---------------------------------------------------------------------------

class TestAddExpenseAmountValidation:

    def test_missing_amount_rerenders_form_not_redirects(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Food",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        # Must re-render (200), not redirect (302).
        assert response.status_code == 200

    def test_missing_amount_shows_error_in_response(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        html = response.data.lower()
        assert b"amount" in html

    def test_missing_amount_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    def test_zero_amount_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "0", "category": "Food",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_zero_amount_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "0", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    def test_negative_amount_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "-50", "category": "Food",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_negative_amount_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "-50", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    def test_non_numeric_amount_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "abc", "category": "Food",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_non_numeric_amount_shows_error_in_response(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "abc", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        html = response.data.lower()
        assert b"amount" in html

    def test_non_numeric_amount_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "abc", "category": "Food",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    def test_sql_injection_in_amount_does_not_insert(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "1'; DROP TABLE expenses; --",
                "category": "Food",
                "date": "2026-04-30",
                "description": "",
            },
        )
        # If FK-safe parameterised queries are used the table survives; count
        # must still be 0 because the value is non-numeric.
        assert _expense_count(db_file, user_id) == 0


# ---------------------------------------------------------------------------
# POST /expenses/add — validation: missing / invalid category
# ---------------------------------------------------------------------------

class TestAddExpenseCategoryValidation:

    def test_missing_category_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_missing_category_shows_error_in_response(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "",
                  "date": "2026-04-30", "description": ""},
        )
        html = response.data.lower()
        assert b"category" in html

    def test_missing_category_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    def test_category_not_in_allowed_list_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "InvalidCategory",
                  "date": "2026-04-30", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_category_not_in_allowed_list_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "InvalidCategory",
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0

    @pytest.mark.parametrize("bad_category", [
        "food",            # wrong case
        "FOOD",            # all caps
        "food ",           # trailing space
        " Food",           # leading space
        "Groceries",       # plausible but not in list
        "'; DROP TABLE expenses; --",  # injection attempt
    ])
    def test_invalid_category_variants_do_not_insert(self, client, bad_category):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": bad_category,
                  "date": "2026-04-30", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0


# ---------------------------------------------------------------------------
# POST /expenses/add — validation: missing date
# ---------------------------------------------------------------------------

class TestAddExpenseDateValidation:

    def test_missing_date_rerenders_form(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "Food",
                  "date": "", "description": ""},
            follow_redirects=False,
        )
        assert response.status_code == 200

    def test_missing_date_shows_error_in_response(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "Food",
                  "date": "", "description": ""},
        )
        html = response.data.lower()
        assert b"date" in html

    def test_missing_date_does_not_insert_db_row(self, client):
        test_client, db_file = client
        user_id = _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={"amount": "50", "category": "Food",
                  "date": "", "description": ""},
        )
        assert _expense_count(db_file, user_id) == 0


# ---------------------------------------------------------------------------
# POST /expenses/add — form value preservation after validation failure
# ---------------------------------------------------------------------------

class TestAddExpenseFormValuePreservation:

    def test_submitted_amount_is_preserved_after_validation_error(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "999.99", "category": "",
                  "date": "2026-04-30", "description": "My note"},
        )
        assert b"999.99" in response.data

    def test_submitted_category_is_preserved_after_validation_error(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Shopping",
                  "date": "2026-04-30", "description": ""},
        )
        # The selected category value should appear in the rendered HTML so the
        # browser can re-select it.
        assert b"Shopping" in response.data

    def test_submitted_date_is_preserved_after_validation_error(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Food",
                  "date": "2026-03-15", "description": ""},
        )
        assert b"2026-03-15" in response.data

    def test_submitted_description_is_preserved_after_validation_error(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={"amount": "", "category": "Food",
                  "date": "2026-04-30", "description": "Keep this description"},
        )
        assert b"Keep this description" in response.data

    def test_all_fields_preserved_when_only_category_is_invalid(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.post(
            "/expenses/add",
            data={
                "amount": "42.00",
                "category": "NotACategory",
                "date": "2026-04-15",
                "description": "Some details",
            },
        )
        assert b"42.00" in response.data
        assert b"2026-04-15" in response.data
        assert b"Some details" in response.data


# ---------------------------------------------------------------------------
# Profile page — "Add Expense" navigation link
# ---------------------------------------------------------------------------

class TestProfileAddExpenseLink:

    def test_profile_page_contains_link_to_add_expense(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        response = test_client.get("/profile")
        assert response.status_code == 200
        assert b"/expenses/add" in response.data

    def test_new_expense_appears_on_profile_after_add(self, client):
        test_client, db_file = client
        _register_and_login(test_client, db_file)
        test_client.post(
            "/expenses/add",
            data={
                "amount": "88.88",
                "category": "Health",
                "date": "2026-04-29",
                "description": "Physiotherapy session",
            },
            follow_redirects=True,
        )
        profile_response = test_client.get("/profile")
        assert b"Physiotherapy session" in profile_response.data \
            or b"88" in profile_response.data
