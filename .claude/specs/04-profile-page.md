# Spec: Profile Page

## Overview
This feature implements the user profile page for the Spendly expense tracker. It displays user-specific information and serves as a central hub for managing personal financial data. The profile page provides authenticated users with a dedicated space to view their account details and navigate to expense management features.

## Depends on
- Step 1: Working directory must be clean ✓
- Step 2: Registration feature must be complete and functional ✓
- Step 3: Login and logout feature must be complete and secured ✓
- Database schema with users and expenses tables ✓
- Authentication middleware and session management ✓

## Routes
- GET /profile — Display user profile page — authenticated access only ✓
- GET /profile/expenses — Display user expenses — authenticated access only (placeholder)

## Database changes
No new tables or columns needed. Uses existing `users` and `expenses` tables.

## Templates
- **Create:** `templates/profile.html` — Profile page template
- **Modify:** `templates/base.html` — Ensure profile navigation link is visible to authenticated users

## Files to change
- `app.py` — Add profile route handlers and expense display logic
- `templates/profile.html` — Create new profile template
- `templates/base.html` — Update navigation to include profile link

## Files to create
- `templates/profile.html` — Profile page template

## New dependencies
No new dependencies. Uses existing Flask session management and database functions.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterized queries only
- Passwords hashed with werkzeug (for any password operations)
- CSS variables used for styling
- All templates extend `base.html`
- Authentication checks on all protected routes
- Use existing database functions (`get_db()`) for all queries

## Definition of done
- [x] User can access /profile page when logged in
- [x] Profile page displays user information (name, email)
- [x] Profile page shows user's expenses in a table
- [x] Profile page includes navigation to add/edit/delete expenses
- [x] Navigation bar shows profile link only when authenticated
- [x] Profile route redirects to login when not authenticated
- [x] All database queries use parameterized statements
- [x] No SQL injection vulnerabilities
- [x] Application starts without errors
- [x] CSS variables are used for styling
- [x] Templates extend base.html correctly
- [x] Expense data is correctly fetched and displayed
- [x] Profile page is responsive and accessible
- [x] Navigation links are correctly highlighted based on current page