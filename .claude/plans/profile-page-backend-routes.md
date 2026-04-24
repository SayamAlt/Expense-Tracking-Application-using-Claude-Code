### Implementation Plan for ProfilePage Backend Routes  

---

#### **CURRENT STATE**  
1. **Existing Authentication Pattern**:  
   - `/profile` route already checks `user_id` in session.  
   - All new routes must replicate this pattern.  

2. **Database Schema**:  
   - `expenses` table has `user_id` foreign key (critical for ownership checks).  
   - Helpers: `get_db()`, `init_db()`, `seed_db()`.  

3. **Existing Routes**:  
   - `/profile/export`: Already queries real expenses from DB.  
   - Stubs: `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` (placeholder text).  

---

#### **WHAT NEEDS TO BE IMPLEMENTED**  
**Route Implementations** (follow existing `/profile` and `/profile/export` patterns):  

1. **GET `/expenses`**  
   - Fetch all expenses for the logged-in user.  
   - **Query**: `SELECT * FROM expenses WHERE user_id = ?` (use `user_id` from session).  
   - Output: Pass data to `/profile.html` template (hydrate UI).  

2. **POST `/expenses/add`**  
   - Create new expense from form data.  
   - **Validation**: Ensure `amount` is numeric, `date` is valid.  
   - **Query**: `INSERT INTO expenses (user_id, amount, category, date, description)` (use `user_id` from session).  
   - Output: Flash success message, redirect to `/profile`.  

3. **GET `/expenses/<id>/edit`**  
   - Fetch specific expense by ID + user ownership.  
   - **Query**: `SELECT * FROM expenses WHERE id = ? AND user_id = ?`.  
   - Output: Render edit form pre-filled with expense data.  

4. **PUT `/expenses/<id>/edit`**  
   - Update existing expense.  
   - **Validation**: Ensure user owns the expense.  
   - **Query**: `UPDATE expenses SET ... WHERE id = ? AND user_id = ?`.  
   - Output: Flash success message, redirect to `/profile`.  

5. **GET `/expenses/<id>/delete`**  
   - Show confirmation page before deletion.  
   - Output: Render confirmation template.  

6. **POST `/expenses/<id>/delete`**  
   - Delete expense.  
   - **Query**: `DELETE FROM expenses WHERE id = ? AND user_id = ?`.  
   - Output: Flash success message, redirect to `/profile`.  

---

#### **DATABASE QUERIES NEEDED**  
- All queries use `user_id` from session to enforce ownership.  
- Parameterized queries (placeholders `?`) to prevent SQL injection.  
- Use `get_db()` helper for database sessions.  

---

#### **FILE STRUCTURE UPDATE (app.py)**  
1. **Auth Guards**: Add `if 'user_id' not in session:` redirects to `/login` for all routes.  
2. **GET `/expenses`**:  
   ```python  
   @app.route('/expenses')  
   def expenses():  
       user_id = session.get('user_id')  
       db = get_db()  
       expenses = db.execute("SELECT * FROM expenses WHERE user_id=?", (user_id,)).fetchall()  
       return render_template('profile.html', expenses=expenses)  
   ```  
3. **POST `/expenses/add`**:  
   ```python  
   @app.route('/expenses/add', methods=['POST'])  
   def add_expense():  
       user_id = session.get('user_id')  
       # Validate form data  
       db = get_db()  
       db.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",  
                  (user_id, amount, category, date, description))  
       flash("Expense added!")  
       return redirect(url_for('profile'))  
   ```  
4. **GET/PUT/DELETE Routes**: Follow similar patterns with owner checks.  
5. **Update Stubs**: Replace placeholder text with functional code.  

---

#### **TESTING VERIFICATION**  
1. **Authentication**:  
   - Logged-out users redirected to `/login` for all routes.  
2. **Data Ownership**:  
   - Users cannot access/modify other users' expenses (verified via `user_id` in WHERE clauses).  
3. **CRUD Functionality**:  
   - Add/Edit/Delete expenses persist in the database.  
4. **UI Integration**:  
   - Fetched expenses populate `/profile.html` correctly.  

---

### Critical Files for Implementation  
- `/Users/sayamkumar/Desktop/Data Science/Claude Code/expense-tracker/app.py`  
  (Update routes, add queries, authentication checks)  
- `/Users/sayamkumar/Desktop/Data Science/Claude Code/expense-tracker/templates/profile.html`  
  (Replace hardcoded data with `{{ expenses }}` loop)  

*(Note: Templates are mentioned for clarity, but no changes are needed as per the user’s request.)*