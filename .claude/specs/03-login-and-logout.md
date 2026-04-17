---
# Spec: Login and Logout (FULLY IMPLEMENTED)

## Overview
This feature implements user authentication via login and logout functionality for the Spendly expense tracker. It allows users to securely access their personal expense data after registering, and provides a way to end their session. This is essential for multi-user support and security.

## Status: ✅ FULLY IMPLEMENTED AND SECURED

## Depends on
- Step 1: Working directory must be clean ✓
- Step 2: Registration feature must be complete and functional ✓
- Database schema with users table containing id, email, password_hash fields ✓

## Routes (Fully Implemented)
- GET /login — Display login form — public access ✓
- POST /login — Handle login submission — public access ✓
- GET /logout — Handle logout — authenticated access only ✓

## Database changes
No new tables or columns needed. Uses existing `users` table with id, email, and password_hash columns.

## Templates (Created/Modified)
- **Created: `templates/login.html`** — Login form template ✓
- **Modified: `templates/base.html`** — Update navigation to show/hide login/logout links ✓

## Files Changed
- `app.py` — Added login/logout route handlers, session management, access control ✓
- `templates/login.html` — Created new login form template ✓
- `templates/base.html` — Updated navigation bar to show/hide auth links ✓

## New dependencies
No new dependencies. Uses Flask's session management and existing werkzeug security functions.

## Implementation Details

### Backend (app.py)
1. Added imports: `session`, `flash` from flask; `check_password_hash` from werkzeug.security
2. Added secret key: `app.secret_key = 'dev-secret-key-change-in-production'`
3. Implemented POST /login:
   - Validates email and password fields
   - Prevents logged-in users from accessing login page
   - Queries database with parameterized query: `SELECT id, password_hash FROM users WHERE email = ?`
   - Verifies password with `check_password_hash`
   - Stores user_id in session on success
   - Shows flash messages
   - Redirects to landing page after successful login
4. Implemented GET /login:
   - Prevents logged-in users from accessing login page
   - Displays login form
5. Implemented /logout:
   - Prevents logged-out users from accessing logout page
   - Clears session
   - Shows flash message
   - Redirects to landing page
6. Updated protected routes (/profile, /expenses/add, etc.) to check authentication

### Templates
- **login.html**: Login form with email/password fields, error display, prevents access when logged in
- **base.html**: Dynamic navigation showing Login/Logout based on session state

## Definition of Done - All Items ✓
- [x] User can access /login page and see login form (when not logged in)
- [x] User can submit login form with valid credentials
- [x] Successful login redirects to landing page
- [x] Failed login shows appropriate error message
- [x] User can logout via /logout route (when logged in)
- [x] After logout, user is redirected to landing page
- [x] Navigation bar shows/hides login/logout links appropriately based on auth state
- [x] Session is properly managed (logged in state persists, cleared on logout)
- [x] All database queries use parameterized statements
- [x] Passwords are verified against hashed values
- [x] No SQL injection vulnerabilities
- [x] Application starts without errors
- [x] CSS variables are used for styling
- [x] Access control: logged-in users cannot access login page
- [x] Access control: logged-out users cannot access logout page
- [x] Protected routes redirect to login when not authenticated

## Security Features
- Secret key for session management
- Password hashing with werkzeug (pbkdf2:sha256)
- Parameterized SQL queries (prevents SQL injection)
- Session-based authentication
- Session clearing on logout
- Authentication checks on all protected routes
- Access control on auth pages (prevent logged-in users from logging in again)

## Test Results - ALL PASSING ✓
- ✓ Login page loads when not logged in
- ✓ Login page redirects when already logged in
- ✓ Invalid login shows error message
- ✓ Valid login redirects to landing page
- ✓ Profile accessible after login
- ✓ Logout clears session and redirects to landing
- ✓ Logout page redirects when already logged out
- ✓ Profile redirects to login when not logged in
- ✓ Protected routes redirect to login when not authenticated
- ✓ Navigation shows correct links based on auth state

## Usage Example
```bash
# Start the application
python3 app.py

# Access login page
curl http://localhost:5001/login

# Login
curl -X POST http://localhost:5001/login \
  -d "email=demo@spendly.com&password=demo123"

# Access protected route
curl http://localhost:5001/profile

# Logout
curl http://localhost:5001/logout
```