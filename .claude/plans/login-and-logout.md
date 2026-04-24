# Implementation Plan: Login and Logout Feature

## Context
This plan outlines the implementation of login and logout functionality for the Spendly expense tracker application. The feature builds upon the completed registration feature (Step 2) and database setup (Step 1).

## Phase 1: Codebase Analysis Summary

### Existing Architecture
- **Framework**: Flask application
- **Database**: SQLite with SQLAlchemy ORM not used (raw SQL with parameterized queries)
- **User Management**:
  - Users table with id, email, password_hash columns
  - Password hashing using werkzeug.security.generate_password_hash
  - Registration already implemented with validation and email uniqueness check
- **Current Routes**:
  - GET /login - displays login form (stub)
  - POST /login - not implemented
  - GET /logout - stub message
  - Session management: Not yet implemented
- **Templates**:
  - base.html - main template with navigation
  - register.html - registration form
  - login.html exists but is a stub

### Key Patterns to Follow
1. Use Flask sessions for authentication state management
2. Parameterized SQL queries only (no string formatting)
3. Password verification using werkzeug.security.check_password_hash
4. Redirect after login/logout with appropriate flash messages
5. Navigation shows/hides auth links based on session state
6. All templates extend base.html

## Implementation Approach

### Step 1: Backend Implementation (app.py)
**Files to modify**: app.py

**Changes needed**:
1. Import session and flash from flask
2. Implement POST /login route:
   - Get email and password from form
   - Query database for user with matching email using parameterized query
   - Verify password hash using check_password_hash
   - If valid: store user id in session, redirect to profile/expenses
   - If invalid: show error message and redirect to login page
3. Implement GET /login route (already exists, ensure it works)
4. Implement GET /logout route:
   - Clear session data
   - Redirect to landing page
5. Update session-based route protection (profile, expenses routes)

### Step 2: Template Implementation
**Files to create/modify**:

1. **Create: templates/login.html**
   - Extend base.html
   - Form with email and password fields
   - Display error messages if present
   - Link to registration page for new users

2. **Modify: templates/base.html**
   - Update navigation to show/hide login/logout links
   - Show login link when user not logged in
   - Show logout link and user info when logged in
   - Use CSS variables for styling consistency

### Step 3: Security Considerations
- All database queries must use parameterized statements
- Passwords must be verified against hash, never stored or compared in plain text
- Session should store minimal user information (user_id)
- Implement proper redirect after authentication to prevent open redirect vulnerabilities
- Use flash messages for user feedback

## Verification Plan

### Test Cases
1. Access /login page - should display login form
2. Submit login with invalid credentials - should show error
3. Submit login with valid credentials - should redirect and set session
4. Access protected route after login - should work
5. Access /logout - should clear session and redirect
6. Verify session is cleared after logout
7. Verify navigation shows correct links (login when logged out, logout when logged in)

### Manual Testing Steps
1. Start the application
2. Navigate to /login
3. Attempt login with demo@spendly.com / demo123
4. Verify redirect to profile or dashboard
5. Check that navigation shows logout link
6. Click logout
7. Verify session is cleared and redirected to landing/login page

## Dependencies
- No new dependencies required
- Uses existing: flask, werkzeug, sqlite3

## Risk Assessment
- Low risk: Following established patterns from registration feature
- Medium risk: Session management requires careful implementation
- Mitigation: Use Flask's built-in session management, follow security best practices