# Spec: Add Expense

## Overview
This feature gives logged-in users a dedicated page to add a new expense. Currently `GET /expenses/add` redirects straight back to `/profile` with no form, so there is no way to actually submit an expense through the UI. This step creates `templates/add_expense.html` with a proper form (amount, category, date, description) and updates the route so that `GET` renders the form and `POST` validates, inserts, and redirects. The backend POST logic is already partially wired in `app.py` and just needs to be aligned with the new template.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must exist)
- Step 3: Login + Logout (session must be set; route must be protected)
- Step 4: Profile page (`/profile` must exist as the redirect target after a successful add)

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the new expense, redirect to `/profile` on success — logged-in only

## Database changes
No database changes. The `expenses` table already has all required columns:
`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`.

## Templates
- **Create:** `templates/add_expense.html` — dedicated form page with:
  - Amount input (number, step="0.01", min="0.01", required)
  - Category select with predefined options: Food, Transport, Bills, Health, Entertainment, Shopping, Other
  - Date input (type="date", defaults to today, required)
  - Description textarea (optional)
  - Submit button ("Add Expense")
  - Cancel link back to `url_for('profile')`
  - Flash message display for validation errors
- **Modify:** `templates/profile.html` — add an "Add Expense" button/link pointing to `url_for('add_expense')` so users can navigate to the new page

## Files to change
- `app.py` — update `GET /expenses/add` to render `add_expense.html` instead of redirecting to profile; keep POST logic but render `add_expense.html` with errors instead of flashing and redirecting on validation failure
- `templates/profile.html` — add "Add Expense" navigation button

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Unauthenticated access to `GET` or `POST /expenses/add` must redirect to `/login`
- Amount must be validated as a positive float server-side; the `<input type="number">` alone is not sufficient
- Category must be one of the predefined values — validate server-side
- Date must be a non-empty string in YYYY-MM-DD format — validate server-side
- On validation failure, re-render the form with the submitted values pre-filled and errors displayed (do not flash-and-redirect)
- On success, flash a success message and redirect to `url_for('profile')`

## Definition of done
- [ ] `GET /expenses/add` renders a form with amount, category, date, and description fields
- [ ] The date field defaults to today's date
- [ ] Submitting a valid form inserts the expense and redirects to `/profile` with a success flash
- [ ] The new expense appears in the expense list on the profile page
- [ ] Submitting with a missing or zero amount shows a validation error on the form (no redirect)
- [ ] Submitting with a missing category shows a validation error on the form
- [ ] Submitting with a missing date shows a validation error on the form
- [ ] After a validation error, previously entered values are pre-filled in the form
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] The profile page has an "Add Expense" button that navigates to `/expenses/add`
