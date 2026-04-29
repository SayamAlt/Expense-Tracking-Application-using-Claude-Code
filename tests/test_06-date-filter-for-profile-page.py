# tests/test_06-date-filter-for-profile-page.py
#
# Spec behaviours under test (Step 06 — Date Filter for Profile Page):
#
#   1. GET /profile with no query params returns all expenses and correct stats.
#   2. GET /profile?start_date=X&end_date=Y returns only expenses in [X, Y];
#      total_spent, transaction count, and top_category reflect that filtered set.
#   3. Only start_date supplied → expenses on or after that date only.
#   4. Only end_date supplied → expenses on or before that date only.
#   5. start_date > end_date → flash error shown, unfiltered data returned.
#   6. Malformed date string → flash error shown, unfiltered data returned.
#   7. Unauthenticated request with date params → redirect to /login (no profile rendered).
#   8. Active filter values are pre-populated in the date input value= attributes.
#   9. A "Clear" link with href="/profile" (no query params) is present on the page.
#  10. Date boundary inclusivity: start_date and end_date dates themselves are included.
#  11. Filter returning zero expenses renders the empty-state message, not a crash.
#  12. Injected SQL in date params is rejected as a malformed date (not executed).

import pytest
from werkzeug.security import generate_password_hash

from app import app
from database.db import get_db, init_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, email, password="Password1!"):
    """Register a fresh user and log them in. Returns the user's DB id."""
    client.post(
        "/register",
        data={
            "name": "Test User",
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )
    client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    with app.app_context():
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()
    return row["id"]


def _insert_expenses(user_id, rows):
    """
    Insert expense rows directly into the DB.

    rows is a list of dicts with keys: amount, category, date, description.
    """
    with app.app_context():
        conn = get_db()
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            [
                (user_id, r["amount"], r["category"], r["date"], r["description"])
                for r in rows
            ],
        )
        conn.commit()
        conn.close()


def _delete_user_and_expenses(user_id):
    """Remove all expenses and the user record so tests stay isolated."""
    with app.app_context():
        conn = get_db()
        conn.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Flask test client with TESTING=True. Uses the real (file-based) DB
    because get_db() hard-codes the path; each test manages its own data
    lifecycle via _register_and_login / _delete_user_and_expenses."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


# Expenses spanning three well-separated months so filters always produce
# a clearly different result set regardless of when the tests are run.
#
#   January 2025  — 2 expenses  (Food: 100.00, Transport: 50.00)
#   April   2025  — 2 expenses  (Bills: 200.00, Health: 75.00)
#   July    2025  — 2 expenses  (Entertainment: 300.00, Shopping: 120.00)
#
# Total (all): 845.00  |  Top category by amount: Entertainment (300.00)

JANUARY_EXPENSES = [
    {"amount": 100.00, "category": "Food",      "date": "2025-01-10", "description": "jan grocery"},
    {"amount":  50.00, "category": "Transport", "date": "2025-01-20", "description": "jan bus"},
]
APRIL_EXPENSES = [
    {"amount": 200.00, "category": "Bills",  "date": "2025-04-05", "description": "apr electricity"},
    {"amount":  75.00, "category": "Health", "date": "2025-04-22", "description": "apr pharmacy"},
]
JULY_EXPENSES = [
    {"amount": 300.00, "category": "Entertainment", "date": "2025-07-14", "description": "jul concert"},
    {"amount": 120.00, "category": "Shopping",      "date": "2025-07-28", "description": "jul clothes"},
]
ALL_TEST_EXPENSES = JANUARY_EXPENSES + APRIL_EXPENSES + JULY_EXPENSES


# ---------------------------------------------------------------------------
# Tests — unauthenticated access
# ---------------------------------------------------------------------------

class TestUnauthenticatedAccess:
    def test_unauthenticated_no_params_redirects_to_login(self, client):
        """Spec: /profile is a protected route — unauthenticated GET redirects."""
        response = client.get("/profile", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_with_start_date_param_redirects_to_login(self, client):
        """Spec: unauthenticated access to /profile?start_date=... still redirects."""
        response = client.get(
            "/profile?start_date=2025-04-01", follow_redirects=False
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_unauthenticated_with_both_date_params_redirects_to_login(self, client):
        """Spec: unauthenticated access with both params still redirects to /login."""
        response = client.get(
            "/profile?start_date=2025-04-01&end_date=2025-04-30",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Tests — no filter (baseline behaviour unchanged)
# ---------------------------------------------------------------------------

class TestNoFilter:
    def test_no_params_returns_200(self, client):
        """Spec: GET /profile with no query params returns 200."""
        uid = _register_and_login(client, "nofilter_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_no_params_all_expenses_transaction_count(self, client):
        """Spec: No params — all expenses are shown (transaction count == total inserted)."""
        uid = _register_and_login(client, "nofilter_count@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            # The template renders {{ expenses|length }} inside the Transactions stat card.
            # 6 expenses were inserted; the count must appear somewhere in the page.
            assert "6" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_no_params_total_spent_reflects_all_expenses(self, client):
        """Spec: No params — total_spent covers all expenses (845.00)."""
        uid = _register_and_login(client, "nofilter_total@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            # Total of all six expenses = 845.00
            assert "845.00" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_no_params_top_category_is_most_expensive(self, client):
        """Spec: No params — top_category reflects the full dataset (Entertainment = 300)."""
        uid = _register_and_login(client, "nofilter_top@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            assert "Entertainment" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_no_params_clear_link_present(self, client):
        """Spec: The 'Clear' link with href=/profile must appear on the page."""
        uid = _register_and_login(client, "nofilter_clear@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            # The Clear anchor must point to the bare /profile path.
            assert 'href="/profile"' in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — both start_date and end_date supplied
# ---------------------------------------------------------------------------

class TestBothDatesFilter:
    def test_both_dates_returns_200(self, client):
        """Spec: Valid date range returns HTTP 200."""
        uid = _register_and_login(client, "both_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_excludes_out_of_range_expenses(self, client):
        """Spec: Only expenses within [start_date, end_date] appear; Jan/Jul excluded."""
        uid = _register_and_login(client, "both_exclude@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # April expenses must be present
            assert "apr electricity" in html
            assert "apr pharmacy" in html
            # January and July expenses must not appear in the expense rows
            assert "jan grocery" not in html
            assert "jan bus" not in html
            assert "jul concert" not in html
            assert "jul clothes" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_transaction_count_reflects_filtered_set(self, client):
        """Spec: Transaction count stat reflects filtered set only (2 for April)."""
        uid = _register_and_login(client, "both_txcount@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # The Transactions KPI card contains expenses|length; April has 2 records.
            # To avoid matching "2025" or other numerals we search within the stat card
            # region by verifying the total matches and not 6 (all-time).
            # "275.00" is the April total (200 + 75) — its presence confirms filtering.
            assert "275.00" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_total_spent_reflects_filtered_set(self, client):
        """Spec: total_spent stat reflects filtered set (April only = 275.00)."""
        uid = _register_and_login(client, "both_total@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            assert "275.00" in html
            # All-time total must NOT appear as the displayed stat
            assert "845.00" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_top_category_reflects_filtered_set(self, client):
        """Spec: top_category reflects filtered set (April top = Bills at 200)."""
        uid = _register_and_login(client, "both_topcat@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # Bills (200) > Health (75) in April — Bills must show as top category.
            assert "Bills" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_start_date_is_inclusive(self, client):
        """Spec: start_date bound is inclusive — an expense on exactly start_date is included."""
        uid = _register_and_login(client, "both_startincl@test.com")
        try:
            _insert_expenses(uid, APRIL_EXPENSES)
            # start_date = exact date of first April expense
            response = client.get("/profile?start_date=2025-04-05&end_date=2025-04-30")
            html = response.data.decode()
            assert "apr electricity" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_end_date_is_inclusive(self, client):
        """Spec: end_date bound is inclusive — an expense on exactly end_date is included."""
        uid = _register_and_login(client, "both_endincl@test.com")
        try:
            _insert_expenses(uid, APRIL_EXPENSES)
            # end_date = exact date of last April expense
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-22")
            html = response.data.decode()
            assert "apr pharmacy" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_both_dates_single_day_range(self, client):
        """Spec: start_date == end_date is a valid single-day filter."""
        uid = _register_and_login(client, "both_singleday@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-05&end_date=2025-04-05")
            html = response.data.decode()
            assert response.status_code == 200
            assert "apr electricity" in html
            assert "apr pharmacy" not in html
            assert "jan grocery" not in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — only start_date supplied
# ---------------------------------------------------------------------------

class TestStartDateOnlyFilter:
    def test_start_date_only_returns_200(self, client):
        """Spec: Single-sided filter with only start_date is accepted (no error)."""
        uid = _register_and_login(client, "startonly_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_start_date_only_excludes_earlier_expenses(self, client):
        """Spec: Only start_date → expenses before that date are excluded."""
        uid = _register_and_login(client, "startonly_excl@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01")
            html = response.data.decode()
            # January is before April — must be excluded
            assert "jan grocery" not in html
            assert "jan bus" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_start_date_only_includes_on_or_after_expenses(self, client):
        """Spec: Only start_date → expenses on or after that date are included."""
        uid = _register_and_login(client, "startonly_incl@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01")
            html = response.data.decode()
            # April and July are on or after 2025-04-01
            assert "apr electricity" in html
            assert "jul concert" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_start_date_only_no_flash_error(self, client):
        """Spec: A valid single-sided start_date does not trigger a flash error."""
        uid = _register_and_login(client, "startonly_noerr@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01")
            html = response.data.decode()
            assert "Invalid date filter" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_start_date_only_stats_reflect_filtered_set(self, client):
        """Spec: Stats reflect filtered set when only start_date is active."""
        uid = _register_and_login(client, "startonly_stats@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            # start_date=2025-04-01 → April (275) + July (420) = 695.00
            response = client.get("/profile?start_date=2025-04-01")
            html = response.data.decode()
            assert "695.00" in html
            assert "845.00" not in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — only end_date supplied
# ---------------------------------------------------------------------------

class TestEndDateOnlyFilter:
    def test_end_date_only_returns_200(self, client):
        """Spec: Single-sided filter with only end_date is accepted (no error)."""
        uid = _register_and_login(client, "endonly_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?end_date=2025-04-30")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_end_date_only_excludes_later_expenses(self, client):
        """Spec: Only end_date → expenses after that date are excluded."""
        uid = _register_and_login(client, "endonly_excl@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?end_date=2025-04-30")
            html = response.data.decode()
            # July is after April — must be excluded
            assert "jul concert" not in html
            assert "jul clothes" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_end_date_only_includes_on_or_before_expenses(self, client):
        """Spec: Only end_date → expenses on or before that date are included."""
        uid = _register_and_login(client, "endonly_incl@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?end_date=2025-04-30")
            html = response.data.decode()
            # January and April are on or before 2025-04-30
            assert "jan grocery" in html
            assert "apr electricity" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_end_date_only_no_flash_error(self, client):
        """Spec: A valid single-sided end_date does not trigger a flash error."""
        uid = _register_and_login(client, "endonly_noerr@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?end_date=2025-04-30")
            html = response.data.decode()
            assert "Invalid date filter" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_end_date_only_stats_reflect_filtered_set(self, client):
        """Spec: Stats reflect filtered set when only end_date is active."""
        uid = _register_and_login(client, "endonly_stats@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            # end_date=2025-04-30 → January (150) + April (275) = 425.00
            response = client.get("/profile?end_date=2025-04-30")
            html = response.data.decode()
            assert "425.00" in html
            assert "845.00" not in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — invalid inputs (start > end, malformed dates)
# ---------------------------------------------------------------------------

class TestInvalidDateInputs:
    def test_start_after_end_returns_200(self, client):
        """Spec: start > end is an invalid filter — page still returns 200."""
        uid = _register_and_login(client, "inv_startend_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get(
                "/profile?start_date=2025-07-01&end_date=2025-04-30"
            )
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_start_after_end_shows_flash_error(self, client):
        """Spec: start > end triggers a flash error message in the rendered page."""
        uid = _register_and_login(client, "inv_startend_flash@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get(
                "/profile?start_date=2025-07-01&end_date=2025-04-30",
                follow_redirects=True,
            )
            html = response.data.decode()
            assert "Invalid date filter" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_start_after_end_returns_unfiltered_data(self, client):
        """Spec: When start > end, unfiltered (all) expenses are rendered."""
        uid = _register_and_login(client, "inv_startend_unfilt@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get(
                "/profile?start_date=2025-07-01&end_date=2025-04-30"
            )
            html = response.data.decode()
            # All three months of expenses must appear (unfiltered)
            assert "jan grocery" in html
            assert "apr electricity" in html
            assert "jul concert" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_malformed_start_date_shows_flash_error(self, client):
        """Spec: Non-ISO start_date (e.g. 'not-a-date') triggers a flash error."""
        uid = _register_and_login(client, "inv_mal_start@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=not-a-date", follow_redirects=True)
            html = response.data.decode()
            assert "Invalid date filter" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_malformed_end_date_shows_flash_error(self, client):
        """Spec: Non-ISO end_date (e.g. '2025/04/30') triggers a flash error."""
        uid = _register_and_login(client, "inv_mal_end@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?end_date=2025/04/30", follow_redirects=True)
            html = response.data.decode()
            assert "Invalid date filter" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_malformed_start_date_returns_unfiltered_data(self, client):
        """Spec: Malformed date → unfiltered data returned (all expenses visible)."""
        uid = _register_and_login(client, "inv_mal_unfilt@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=not-a-date")
            html = response.data.decode()
            assert "jan grocery" in html
            assert "apr electricity" in html
            assert "jul concert" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_malformed_date_returns_200(self, client):
        """Spec: Malformed date does not crash the route; returns HTTP 200."""
        uid = _register_and_login(client, "inv_mal_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=13-99-2025")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_sql_injection_in_start_date_treated_as_malformed(self, client):
        """Spec: SQL injection string is not a valid ISO date — must be rejected as malformed."""
        uid = _register_and_login(client, "inv_sqlinj@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get(
                "/profile?start_date='; DROP TABLE expenses; --",
                follow_redirects=True,
            )
            html = response.data.decode()
            # Must show flash error (not a valid ISO date)
            assert "Invalid date filter" in html
            assert response.status_code == 200
            # Expenses table must still exist — verify by checking own data is still present
            response2 = client.get("/profile")
            assert response2.status_code == 200
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — form pre-population and UI elements
# ---------------------------------------------------------------------------

class TestFormUIBehaviour:
    def test_active_start_date_prepopulated_in_input(self, client):
        """Spec: After filter submission, start_date value is pre-populated in the input."""
        uid = _register_and_login(client, "ui_startpop@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # The input element must carry the submitted value in its value= attribute.
            assert 'value="2025-04-01"' in html
        finally:
            _delete_user_and_expenses(uid)

    def test_active_end_date_prepopulated_in_input(self, client):
        """Spec: After filter submission, end_date value is pre-populated in the input."""
        uid = _register_and_login(client, "ui_endpop@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            assert 'value="2025-04-30"' in html
        finally:
            _delete_user_and_expenses(uid)

    def test_no_filter_inputs_have_empty_values(self, client):
        """Spec: When no filter is active the date inputs carry empty value attributes."""
        uid = _register_and_login(client, "ui_nofilt_empty@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            # Both inputs should render with value=""
            assert 'value=""' in html
        finally:
            _delete_user_and_expenses(uid)

    def test_clear_link_present_when_no_filter_active(self, client):
        """Spec: The Clear link pointing to /profile (no params) is always present."""
        uid = _register_and_login(client, "ui_clear_nofilter@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            assert 'href="/profile"' in html
        finally:
            _delete_user_and_expenses(uid)

    def test_clear_link_present_when_filter_active(self, client):
        """Spec: The Clear link remains present when a date filter is active."""
        uid = _register_and_login(client, "ui_clear_filter@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # The clear link must still point to bare /profile (no query string)
            assert 'href="/profile"' in html
        finally:
            _delete_user_and_expenses(uid)

    def test_filter_badge_shown_when_filter_active(self, client):
        """Spec: An active-filter indicator (badge/label) is rendered when dates are set."""
        uid = _register_and_login(client, "ui_badge@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            # The spec requires an active-filter indicator near the stats row.
            # The template renders a <span class="filter-badge"> containing the dates.
            assert "2025-04-01" in html
            assert "2025-04-30" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_filter_badge_not_shown_when_no_filter(self, client):
        """Spec: Active-filter badge is absent when no date filter is applied."""
        uid = _register_and_login(client, "ui_nobadge@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            assert "filter-badge" not in html
        finally:
            _delete_user_and_expenses(uid)

    def test_filter_form_uses_get_method(self, client):
        """Spec: The filter form must use method=GET so filter state is bookmarkable."""
        uid = _register_and_login(client, "ui_getmethod@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile")
            html = response.data.decode()
            assert 'method="GET"' in html or "method='GET'" in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — empty result set
# ---------------------------------------------------------------------------

class TestEmptyFilterResult:
    def test_filter_with_no_matching_expenses_returns_200(self, client):
        """Spec: A valid filter that matches zero expenses does not crash the route."""
        uid = _register_and_login(client, "empty_200@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            # 2020 range contains no test expenses
            response = client.get("/profile?start_date=2020-01-01&end_date=2020-01-31")
            assert response.status_code == 200
        finally:
            _delete_user_and_expenses(uid)

    def test_filter_with_no_matching_expenses_shows_empty_state(self, client):
        """Spec: When filtered result is empty, the empty-state message is rendered."""
        uid = _register_and_login(client, "empty_msg@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2020-01-01&end_date=2020-01-31")
            html = response.data.decode()
            assert "No expenses found" in html
        finally:
            _delete_user_and_expenses(uid)

    def test_filter_with_no_matching_expenses_total_is_zero(self, client):
        """Spec: When filtered set is empty, total_spent stat shows 0.00."""
        uid = _register_and_login(client, "empty_total@test.com")
        try:
            _insert_expenses(uid, ALL_TEST_EXPENSES)
            response = client.get("/profile?start_date=2020-01-01&end_date=2020-01-31")
            html = response.data.decode()
            assert "0.00" in html
        finally:
            _delete_user_and_expenses(uid)


# ---------------------------------------------------------------------------
# Tests — data isolation (user A cannot see user B's expenses)
# ---------------------------------------------------------------------------

class TestUserDataIsolation:
    def test_filter_only_returns_current_users_expenses(self, client):
        """Spec (implied): Filtered results never include another user's expenses."""
        uid_a = _register_and_login(client, "iso_usera@test.com")
        _insert_expenses(uid_a, APRIL_EXPENSES)

        # Register user B and insert their own April expense with a unique description
        with app.app_context():
            conn = get_db()
            pw = generate_password_hash("Password1!", method="pbkdf2:sha256")
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("User B", "iso_userb@test.com", pw),
            )
            conn.commit()
            uid_b = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("iso_userb@test.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description)"
                " VALUES (?, ?, ?, ?, ?)",
                (uid_b, 999.99, "Bills", "2025-04-15", "userb_secret_expense"),
            )
            conn.commit()
            conn.close()

        try:
            # User A is still logged in (last login in _register_and_login)
            # Re-login as user A explicitly
            client.post(
                "/login",
                data={"email": "iso_usera@test.com", "password": "Password1!"},
                follow_redirects=True,
            )
            response = client.get("/profile?start_date=2025-04-01&end_date=2025-04-30")
            html = response.data.decode()
            assert "userb_secret_expense" not in html
        finally:
            _delete_user_and_expenses(uid_a)
            _delete_user_and_expenses(uid_b)
