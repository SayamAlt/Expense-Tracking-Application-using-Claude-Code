# Spec: Edit Expense

## Overview
This feature lets logged-in users edit an existing expense. `GET /expenses/<id>/edit` loads the expense (ownership-checked) and pre-fills a form with current values. `POST /expenses/<id>/edit` validates the submitted data and runs an `UPDATE` query, then redirects to `/profile`. If the expense does not exist or belongs to a different user, the route flashes an error and redirects to `/profile`. This step mirrors the Add Expense form but operates on an existing record instead of inserting a new one.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must exist)
- Step 3: Login + Logout (session must be set; route must be protected)
- Step 4: Profile page (`/profile` must exist as the redirect target)
- Step 7: Add Expense (establishes the expense form pattern this step reuses)

## Routes
- `GET /expenses/<int:expense_id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only
- `POST /expenses/<int:expense_id>/edit` — validate and update the expense, redirect to `/profile` on success — logged-in only

## Database changes
No database changes. The `expenses` table already has all required columns:
`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`.

## Templates
- **Create:** `templates/edit_expense.html` — edit form page extending `base.html` with:
  - Amount input (number, step="0.01", min="0.01", required) pre-filled from `form.amount`
  - Category select with predefined options pre-selecting `form.category`
  - Date input (type="date", required) pre-filled from `form.date`
  - Description textarea (optional) pre-filled from `form.description`
  - Submit button ("Save Changes")
  - Cancel link back to `url_for('profile')`
  - Inline error list rendered when `errors` is non-empty
- **Modify:** None — profile page already links to edit via `url_for('edit_expense', expense_id=...)`

## Files to change
- `app.py` — implement `GET /expenses/<int:expense_id>/edit` (render pre-filled form) and `POST` (validate, UPDATE, redirect)

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Ownership enforced in every query: `WHERE id = ? AND user_id = ?` — never fetch by id alone
- Unauthenticated access redirects to `/login`
- Non-existent or unowned expense flashes an error and redirects to `/profile` (do not 404)
- Amount validated as a positive float ≤ 1,000,000 server-side
- Category validated against the `EXPENSE_CATEGORIES` allowlist server-side
- Date validated as a non-empty YYYY-MM-DD string server-side
- On validation failure, re-render the form with submitted values pre-filled and errors displayed (do not flash-and-redirect)
- On success, flash a success message and redirect to `url_for('profile')`

## Definition of done
- [ ] `GET /expenses/<id>/edit` renders a form pre-filled with the expense's existing amount, category, date, and description
- [ ] Submitting a valid form updates the expense and redirects to `/profile` with a success flash
- [ ] The updated values appear in the expense list on the profile page
- [ ] Submitting with a missing or zero amount shows a validation error on the form (no redirect)
- [ ] Submitting with an invalid category shows a validation error on the form
- [ ] Submitting with a missing date shows a validation error on the form
- [ ] After a validation error, the submitted (not original) values are pre-filled in the form
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Attempting to edit another user's expense redirects to `/profile` with an error flash
- [ ] Attempting to edit a non-existent expense redirects to `/profile` with an error flash
