# Spec: Date Filter For Profile Page

## Overview
This feature adds date-range filtering to the profile page so users can narrow the expense list, summary stats, and category breakdown to a specific time window (e.g. this month, last 30 days, or a custom from/to date range). All filtering is handled server-side: the `/profile` route accepts optional `start_date` and `end_date` query parameters, re-runs the database queries with those bounds, and returns the filtered results to the existing `profile.html` template. The UI gains a small filter form above the expense table.

## Depends on
- Step 1: Database setup (expenses table must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)
- Step 4: Profile page (profile.html template must exist)
- Step 5: Backend routes for profile page (live expense data must already be wired up)

## Routes
No new routes. The existing `GET /profile` route is extended to accept optional query parameters:
- `start_date` (YYYY-MM-DD) — lower bound (inclusive) for filtering expenses by date
- `end_date` (YYYY-MM-DD) — upper bound (inclusive) for filtering expenses by date

## Database changes
No database changes. The existing `expenses` table with a `date TEXT` column (YYYY-MM-DD format) is sufficient for range filtering via SQL `BETWEEN` / `>=` / `<=` comparisons.

## Templates
- **Modify:** `templates/profile.html` — add a filter form above the expense table with:
  - A "Start date" date input (`name="start_date"`)
  - An "End date" date input (`name="end_date"`)
  - A "Filter" submit button
  - A "Clear" link that navigates back to `/profile` with no query params
  - Display the active filter range (if any) as a label/badge near the stats row so users know what window they are viewing

## Files to change
- `app.py` — update the `/profile` route to:
  1. Read `start_date` and `end_date` from `request.args`
  2. Validate the dates: both must be valid YYYY-MM-DD strings if present; `start_date` must not be after `end_date`
  3. Build the SQL WHERE clause conditionally to add date bounds
  4. Pass `start_date` and `end_date` back to the template so the form can pre-populate
- `templates/profile.html` — add the filter form and active-filter indicator described above

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Date validation must use the standard library `datetime.date.fromisoformat()` — no external date libraries
- If only one of `start_date` / `end_date` is supplied, apply just that bound (do not reject a single-sided filter)
- If dates are invalid (non-ISO format, start > end), flash an error and render the page with unfiltered data
- Summary stats (total spent, average, top category, category breakdown) must reflect the filtered result set, not all-time data
- The filter form must use `method="GET"` so the filter state is bookmarkable

## Definition of done
- [ ] Visiting `/profile` with no query params shows all expenses (existing behaviour unchanged)
- [ ] Submitting `start_date=2026-04-01&end_date=2026-04-30` returns only expenses in April 2026
- [ ] Total spent, average, and top category stats update to match the filtered expense set
- [ ] The date inputs are pre-populated with the currently active filter values after form submission
- [ ] Clicking "Clear" removes the filter and shows all expenses again
- [ ] Supplying only `start_date` filters to expenses on or after that date
- [ ] Supplying only `end_date` filters to expenses on or before that date
- [ ] Supplying a `start_date` later than `end_date` shows a flash error and unfiltered data
- [ ] Supplying a malformed date (e.g. `start_date=not-a-date`) shows a flash error and unfiltered data
- [ ] Unauthenticated access to `/profile?start_date=...` still redirects to `/login`
