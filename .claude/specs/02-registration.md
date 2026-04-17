---
# Spec: Registration

## Overview
The registration feature will allow new users to create accounts in the Spendly expense tracker. It will handle form submission, password hashing, and basic validation to ensure data integrity. This feature is critical for onboarding new users and is the first step in the Spendly roadmap for user management.

## Depends on
- Step 1: Working directory must be clean

## Routes
- POST /register - Handles user registration form submission. Requires public access.

## Database changes
- No new tables or columns needed. Will validate against existing `users` table in `database/db.py`.

## Templates
- **Create:** `templates/register.html` - New registration form template
- **Modify:** `base.html` - Ensure registration form extends base template

## Files to change
- `app.py` (add registration route and handler)
- `templates/register.html` (create new template)
- `base.html` (update extension logic)

## Files to create
- `templates/register.html`

## New dependencies
- No new dependencies

## Rules for implementation
- No SQLAlchemy or ORMs
- Passwords hashed with werkzeug
- CSS variables used for styling
- All templates must extend `base.html`

## Definition of done
- User can successfully register via the form
- Registration data persists in the database
- No SQL injection vulnerabilities
- Passwords are properly hashed
- Form validation works as expected
---
