# Spec: Delete Expense

## Overview
This feature lets logged-in users permanently delete an existing expense. `GET /expenses/<id>/delete` loads the expense (ownership-checked) and renders a confirmation page showing the expense details. `POST /expenses/<id>/delete` executes the `DELETE` query and redirects to `/profile`. If the expense does not exist or belongs to a different user, the route flashes an error and redirects to `/profile`. The confirmation step prevents accidental deletion triggered by prefetch or link crawlers.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must exist)
- Step 3: Login + Logout (session must be set; route must be protected)
- Step 4: Profile page (`/profile` must exist as the redirect target and must link to delete)
- Step 7: Add Expense (expenses must exist to delete)
- Step 8: Edit Expense (establishes the expense ownership-check pattern this step reuses)

## Routes
- `GET /expenses/<int:expense_id>/delete` — render confirmation page showing expense details — logged-in only
- `POST /expenses/<int:expense_id>/delete` — delete the expense and redirect to `/profile` — logged-in only

## Database changes
No database changes. Deletion operates on the existing `expenses` table using a parameterised `DELETE` query.

## Templates
- **Create:** `templates/delete_expense.html` — confirmation page extending `base.html` with:
  - Read-only display of the expense: amount (formatted via `currency` filter), category, date, description (shown only if non-empty)
  - Warning text: "This cannot be reversed"
  - A `<form method="POST">` with a single "Yes, Delete Expense" submit button (styled as danger)
  - Cancel link back to `url_for('profile')`
- **Modify:** None — profile page already links to delete via `url_for('delete_expense', expense_id=...)`

## Files to change
- `app.py` — implement `GET /expenses/<int:expense_id>/delete` (render confirmation) and `POST` (DELETE query, redirect)

## Files to create
- `templates/delete_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()` only
- Parameterised queries only — never f-strings or string concatenation in SQL
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Ownership enforced in every query: `WHERE id = ? AND user_id = ?` — never delete by id alone
- Unauthenticated access redirects to `/login`
- Non-existent or unowned expense flashes an error and redirects to `/profile`
- Deletion must only happen via `POST` — `GET` renders confirmation only; it never mutates state
- Use the `currency` template filter for amount display (already registered in `app.py`)
- On successful deletion, flash a success message and redirect to `url_for('profile')`

## Definition of done
- [ ] `GET /expenses/<id>/delete` renders a confirmation page showing the expense's amount, category, date, and description
- [ ] The confirmation page does not delete anything — it only shows a form
- [ ] Submitting the confirmation form (POST) deletes the expense and redirects to `/profile` with a success flash
- [ ] The deleted expense no longer appears in the expense list on the profile page
- [ ] Visiting `/expenses/<id>/delete` while logged out redirects to `/login`
- [ ] Attempting to delete another user's expense redirects to `/profile` with an error flash
- [ ] Attempting to delete a non-existent expense redirects to `/profile` with an error flash
- [ ] The cancel link on the confirmation page returns to `/profile` without deleting anything
- [ ] Amount on confirmation page is formatted with the `currency` filter (e.g. `$45.50` not `45.5`)
