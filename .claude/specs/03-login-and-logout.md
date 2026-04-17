---
# Spec: Login and Logout

## Overview
This feature implements user authentication via login and logout functionality for the Spendly expense tracker. It allows users to securely access their personal expense data after registering, and provides a way to end their session. This is essential for multi-user support and security.

## Depends on
- Step 1: Working directory must be clean
- Step 2: Registration feature must be complete and functional
- Database schema with users table containing id, email, password_hash fields

## Routes
- GET /login — Display login form — public access
- POST /login — Handle login submission — public access
- GET /logout — Handle logout — logged-in access

## Database changes
No new tables or columns needed. Will use existing `users` table with id, email, and password_hash columns.

## Templates
- **Create:** `templates/login.html` — Login form template
- **Modify:** `base.html` — Update navigation to show/hide login/logout links

## Files to change
- `app.py` — Add login and logout route handlers, session management
- `templates/login.html` — Create new login form template
- `templates/base.html` — Update navigation bar to show/hide auth links

## Files to create
- `templates/login.html` — Login form template

## New dependencies
No new dependencies. Uses Flask's session management and existing werkzeug security functions.

## Rules for implementation
- No SQLAlchemy or ORMs
- Use parameterized queries only
- Passwords hashed with werkzeug
- Use Flask session for authentication state
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Implement proper redirect after login/logout
- Secure session management with appropriate flash messages

## Definition of done
- [ ] User can access /login page and see login form
- [ ] User can submit login form with valid credentials
- [ ] Successful login redirects to a protected page (e.g., /profile or /expenses)
- [ ] Failed login shows appropriate error message
- [ ] User can logout via /logout route
- [ ] After logout, user is redirected to login or landing page
- [ ] Navigation bar shows/hides login/logout links appropriately based on auth state
- [ ] Session is properly managed (logged in state persists, cleared on logout)
- [ ] All database queries use parameterized statements
- [ ] Passwords are verified against hashed values
- [ ] No SQL injection vulnerabilities
- [ ] Application starts without errors
- [ ] CSS variables are used for styling