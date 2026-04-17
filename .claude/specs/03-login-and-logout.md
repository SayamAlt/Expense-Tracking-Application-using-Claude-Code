---
# Spec: Login and Logout (IMPLEMENTED)

## Overview
This feature implements user authentication via login and logout functionality for the Spendly expense tracker. It allows users to securely access their personal expense data after registering, and provides a way to end their session. This is essential for multi-user support and security.

## Status: ✅ IMPLEMENTED

## Depends on
- Step 1: Working directory must be clean ✓
- Step 2: Registration feature must be complete and functional ✓
- Database schema with users table containing id, email, password_hash fields ✓

## Routes (Implemented)
- GET /login — Display login form — public access ✓
- POST /login — Handle login submission — public access ✓
- GET /logout — Handle logout — logged-in access ✓

## Database changes
No new tables or columns needed. Uses existing `users` table with id, email, and password_hash columns.

## Templates (Created/Modified)
- **Created: `templates/login.html`** — Login form template ✓
- **Modified: `templates/base.html`** — Update navigation to show/hide login/logout links ✓

## Files Changed
- `app.py` — Added login/logout route handlers, session management ✓
- `templates/login.html` — Created new login form template ✓
- `templates/base.html` — Updated navigation bar to show/hide auth links ✓

## New dependencies
No new dependencies. Uses Flask's session management and existing werkzeug security functions.

## Implementation Details

### Backend (app.py)
1. Added imports: `session`, `flash` from flask; `check_password_hash` from werkzeug.security
2. Added secret key: `app.secret_key = 'dev-secret-key-change-in-production'`
3. Implemented POST /login:
   - Validates email and password
   - Queries database with parameterized query: `SELECT id, password_hash FROM users WHERE email = ?`
   - Verifies password with `check_password_hash`
   - Stores user_id in session on success
   - Shows flash messages
   - Redirects appropriately
4. Implemented GET /login: Displays login form
5. Implemented /logout: Clears session, shows flash, redirects to landing
6. Updated protected routes (/profile, /expenses/add, etc.) to check authentication

### Templates
- **login.html**: Login form with email/password fields, error display
- **base.html**: Dynamic navigation showing Login/Logout based on session state

## Definition of Done - All Items ✓
- [x] User can access /login page and see login form
- [x] User can submit login form with valid credentials
- [x] Successful login redirects to a protected page (e.g., /profile)
- [x] Failed login shows appropriate error message
- [x] User can logout via /logout route
- [x] After logout, user is redirected to login or landing page
- [x] Navigation bar shows/hides login/logout links appropriately based on auth state
- [x] Session is properly managed (logged in state persists, cleared on logout)
- [x] All database queries use parameterized statements
- [x] Passwords are verified against hashed values
- [x] No SQL injection vulnerabilities
- [x] Application starts without errors
- [x] CSS variables are used for styling

## Testing Results
All tests passed successfully:
- ✓ Login page loads (200)
- ✓ Invalid login shows error message
- ✓ Valid login redirects to profile (302)
- ✓ Profile accessible after login (200)
- ✓ Logout clears session and redirects (302)
- ✓ Session cleared after logout
- ✓ Profile access without login redirects to login (302)
- ✓ Protected routes redirect when not authenticated
- ✓ Navigation shows correct links based on auth state

## Security Features
- Secret key for session management
- Password hashing with werkzeug (pbkdf2:sha256)
- Parameterized SQL queries (prevents SQL injection)
- Session-based authentication
- Session clearing on logout
- Authentication checks on all protected routes