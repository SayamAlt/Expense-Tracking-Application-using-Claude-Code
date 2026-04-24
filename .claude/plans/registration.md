# Implementation Plan: Registration Feature for Spendly Expense Tracker

## Context
This plan details the implementation of the registration feature as specified in `.claude/specs/02-registration.md`. The feature will allow new users to create accounts in the Spendly expense tracker application.

## Overview
The registration feature enables new users to create accounts through a form submission process with password hashing, validation, and data persistence to the SQLite database.

## Implementation Plan

### 1. File Modifications Required

#### 1.1 Create Template: `templates/register.html`
**Status:** File to be created

The registration form template must:
- Extend `base.html` (as per rule: all templates must extend base.html)
- Include a form with POST method to `/register` endpoint
- Form fields:
  - Full name (text input, required)
  - Email address (email input, required)
  - Password (password input, required, min 8 characters)
- Include CSRF protection placeholder
- Display error messages if present (for existing validation feedback)
- Include "Create account" submit button
- Include link to login page for existing users
- Use CSS variables for styling consistency

#### 1.2 Modify: `app.py`
**Status:** Add registration route handler

Add a new POST route `/register` that:
- Validates incoming form data (name, email, password)
- Performs validation checks:
  - All fields are required
  - Email format validation
  - Password minimum length (8 characters)
  - Email uniqueness check against database
- Hashes password using werkzeug.security (as per rule: passwords hashed with werkzeug)
- Inserts new user into `users` table using raw SQL (no ORMs as per rule)
- Returns appropriate responses (redirect on success, render with error on failure)

#### 1.3 Modify: `base.html`
**Status:** Update navigation and extension logic

Updates needed:
- Ensure registration form navigation link exists (already present: "Get started" link)
- Verify template extends logic is correct
- Ensure CSS variables are properly linked for consistent styling

### 2. Technical Requirements

#### 2.1 Security Requirements
- **Password Hashing:** Use `werkzeug.security.generate_password_hash()` with appropriate method (preferably pbkdf2:sha256 or similar)
- **SQL Injection Prevention:** Use parameterized queries exclusively (as per rule: No SQL injection vulnerabilities)
- **Form Validation:** Validate all inputs before database operations
- **HTTPS Consideration:** Ensure passwords are transmitted securely

#### 2.2 Database Operations
- **Table:** Use existing `users` table in `database/db.py`
- **Columns:** id, name, email, password_hash, created_at
- **Constraints:** email must be UNIQUE
- **No schema changes:** Validate against existing structure (as per rule: No new tables or columns needed)

#### 2.3 Validation Rules
- **Name:** Required, non-empty string
- **Email:** Required, valid email format, unique in database
- **Password:** Required, minimum 8 characters
- **Error Handling:** Display meaningful error messages to users

### 3. Implementation Steps

#### Step 1: Create Registration Template
1. Create `templates/register.html`
2. Implement form with proper HTML structure
3. Add validation attributes (required, email type, minlength)
4. Extend base.html template structure
5. Include error display area for form validation messages
6. Use CSS variables for consistent styling

#### Step 2: Add Registration Route
1. Import necessary modules in app.py (already has werkzeug imported in db.py)
2. Create POST route handler for `/register`
3. Implement form data extraction and validation
4. Add database connection and user insertion logic
5. Implement password hashing
6. Add proper error handling and redirect logic

#### Step 3: Update Base Template (if needed)
1. Verify navigation links are properly structured
2. Ensure CSS is properly linked
3. Check template inheritance chain

#### Step 4: Testing
1. Test form submission with valid data
2. Test form submission with invalid data
3. Test duplicate email handling
4. Verify password hashing in database
5. Test SQL injection prevention
6. Verify user creation in database

### 4. Integration Points

#### 4.1 Existing Components
- **Database:** `database/db.py` - `users` table structure
- **Templates:** `templates/base.html` - template inheritance base
- **Application:** `app.py` - main application routing

#### 4.2 Dependencies
- **No new dependencies required** (as per spec)
- Use existing werkzeug installation for password hashing
- Use existing SQLite database connection

### 5. Security Considerations

#### 5.1 Input Validation
- Server-side validation required (client-side is not sufficient)
- Validate email format using regex or built-in validators
- Validate password strength (minimum length)

#### 5.2 Database Security
- Use parameterized queries: `cursor.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hash))`
- Never concatenate user input into SQL strings
- Handle database constraint violations gracefully

#### 5.3 Password Security
- Use strong hashing algorithm (pbkdf2:sha256 recommended)
- Never store plain text passwords
- Consider adding salt (werkzeug handles this automatically)

### 6. Definition of Done Checklist

- [ ] User can successfully register via the form
- [ ] Registration data persists in the database correctly
- [ ] No SQL injection vulnerabilities exist
- [ ] Passwords are properly hashed (verify in database)
- [ ] Form validation works as expected
- [ ] Error messages display appropriately for invalid input
- [ ] Existing users can navigate to registration page
- [ ] Template extends base.html correctly
- [ ] All templates use CSS variables for styling
- [ ] No new dependencies installed

### 7. Testing Strategy

#### 7.1 Manual Testing
1. Access `/register` route - verify form displays
2. Submit empty form - verify validation errors
3. Submit with invalid email format - verify validation
4. Submit with short password - verify validation
5. Submit valid data - verify user creation
6. Verify hashed password in database
7. Try duplicate email - verify error handling

#### 7.2 Database Verification
```python
# After registration, verify user exists
conn = get_db()
user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
# Verify password_hash is hashed (not plain text)
# Verify created_at timestamp exists
```

#### 7.3 Security Testing
- Attempt SQL injection via form fields
- Verify passwords are not stored in plain text
- Verify error messages don't leak sensitive information

### 8. Code Quality Guidelines

#### 8.1 Implementation Rules (Per Spec)
- [ ] No SQLAlchemy or ORMs used
- [ ] Passwords hashed with werkzeug
- [ ] CSS variables used for styling
- [ ] All templates extend base.html
- [ ] No new dependencies added

#### 8.2 Code Structure
- Keep route handler clean and focused
- Use proper error handling
- Return appropriate HTTP status codes
- Use consistent naming conventions

### 9. Potential Issues and Solutions

#### Issue 9.1: Duplicate Email Registration
- **Solution:** Catch database constraint violation and return user-friendly error

#### Issue 9.2: Form Validation Errors
- **Solution:** Pass error messages to template and display appropriately

#### Issue 9.3: Password Hashing Compatibility
- **Solution:** Use werkzeug's generate_password_hash which is standard

### 10. Verification Steps

1. **Functional Verification:**
   - Navigate to `/register` and verify form loads
   - Register new user with valid data
   - Verify redirect or success message
   - Check database for new user record
   - Verify password is hashed

2. **Security Verification:**
   - Attempt SQL injection: `' OR '1'='1`
   - Verify password storage is hashed
   - Check for proper error handling

3. **Integration Verification:**
   - Verify navigation from login to register
   - Verify consistent styling with base template
   - Test across different form inputs

## Risk Assessment
- **Low Risk:** Feature uses existing database structure and no new dependencies
- **Medium Risk:** Security implementation must be correct (password hashing, SQL injection prevention)
- **Low Risk:** Template extension is straightforward

## Timeline
This implementation can be completed in a single session with the following estimated time:
- Template creation: 30 minutes
- Route implementation: 60 minutes
- Testing and validation: 30 minutes
- Total: ~2 hours