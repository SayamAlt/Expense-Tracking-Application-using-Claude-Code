---
# Spec: Backend Routes for Profile Page

## Overview
Implements backend routes for expense management including adding, editing, and deleting expenses. Builds upon existing authentication routes to provide authenticated users with expense tracking capabilities through a series of CRUD operations on profile expenses. This feature advances the profile page from a static display to a dynamic interface connected to real user data.

## Depends on
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)

## Routes
- GET /expenses - Fetch all expenses for user — logged-in only
- POST /expenses/add - Create new expense — logged-in only
- GET /expenses/<id>/edit - Show form to edit expense — logged-in only
- PUT /expenses/<id>/edit - Update existing expense — logged-in only
- GET /expenses/<id>/delete - Show delete confirmation — logged-in only
- POST /expenses/<id>/delete - Remove expense — logged-in only

## Database changes
- No new tables or columns needed. The existing `expenses` table has `user_id` foreign key referencing `users(id)` for ownership enforcement.

## Templates
- **Modify:** None - all routes either return JSON or render existing `profile.html` template.

## Files to change
- `app.py`: Add route handlers for expense CRUD operations and update existing stubs.
- `templates/profile.html`: Update to use dynamic `expenses` data (will be passed from new routes).

## New dependencies
- No new dependencies required.

## Rules for implementation
1. All SQL operations use parameterized queries (`?` placeholders) only
2. Authentication validation via session checks (`if "user_id" not in session:`)
3. Parameter validation for form inputs (amount numeric, etc.)
4. Error handling returns appropriate HTTP responses
5. Success responses return JSON where appropriate, redirects for HTML pages
6. All templates extend `base.html`
7. Password operations use werkzeug hashing (already used in registration/login)

## Definition of done
Each item must be testable via Flask app:
- [ ] All routes require authentication and reject unauthenticated access
- [ ] GET /expenses renders expenses list in profile template
- [ ] POST /expenses/add adds expense to database
- [ ] PUT /expenses/<id>/edit updates expense correctly
- [ ] DELETE /expenses/<id>/delete removes expense successfully
- [ ] User cannot access/modify another user's expenses (enforced via user_id in WHERE clauses)