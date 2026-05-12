# Plan: Edit Expense (Step 08)

## Context
Users can add expenses but have no way to correct mistakes. `GET /expenses/<id>/edit` must load the existing expense (owner-checked), pre-fill a form with current values, and let the user submit corrections. `POST` validates and runs an `UPDATE`. Validation rules are identical to Add Expense. Ownership is enforced in every query — never fetch or update by `id` alone. Non-existent or unowned expenses redirect to `/profile` with a flash error rather than 404.

---

## Files to modify

| File | Change |
|---|---|
| `app.py` | Implement `edit_expense` route — GET renders pre-filled form, POST validates and UPDATEs |

## Files to create

| File | Purpose |
|---|---|
| `templates/edit_expense.html` | Edit-expense form page, same layout as `add_expense.html` |

---

## Implementation steps

### 1. Update `app.py` — `edit_expense` route

Replace the stub at `/expenses/<int:expense_id>/edit` with the full implementation. `EXPENSE_CATEGORIES` is already defined at line 12 — reference it directly.

```python
@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, session["user_id"])
    ).fetchone()

    if not expense:
        conn.close()
        flash("Expense not found", "error")
        return redirect(url_for("profile"))

    if request.method == "POST":
        amount_raw  = request.form.get("amount", "").strip()
        category    = request.form.get("category", "")
        date        = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        amount = None
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be positive")
            elif amount > 1_000_000:
                errors.append("Amount cannot exceed $1,000,000")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")

        if not category or category not in EXPENSE_CATEGORIES:
            errors.append("Please select a valid category")
        if not date:
            errors.append("Date is required")
        else:
            try:
                _date.fromisoformat(date)
            except ValueError:
                errors.append("Date must be a valid date (YYYY-MM-DD)")

        if errors:
            conn.close()
            return render_template(
                "edit_expense.html",
                expense=expense,
                errors=errors,
                categories=EXPENSE_CATEGORIES,
                form={"amount": amount_raw, "category": category,
                      "date": date, "description": description},
            )

        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ?"
            " WHERE id = ? AND user_id = ?",
            (amount, category, date, description, expense_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Expense updated successfully!", "success")
        return redirect(url_for("profile"))

    # GET — pre-fill form with current expense values
    conn.close()
    return render_template(
        "edit_expense.html",
        expense=expense,
        errors=[],
        categories=EXPENSE_CATEGORIES,
        form={"amount": expense["amount"], "category": expense["category"],
              "date": expense["date"], "description": expense["description"] or ""},
    )
```

**Key design decisions:**
- `expense` fetched once at the top of the view for both GET and POST — avoids a second DB round-trip
- `conn.close()` called before every `return` including error paths — no connection leak
- `UPDATE` query includes `AND user_id = ?` as a second ownership check — prevents IDOR even if `expense` lookup somehow passed
- On POST validation failure: pass `expense` (original row) alongside `form` (submitted values) so the template can use `expense.id` for the form `action` URL

---

### 2. Create `templates/edit_expense.html`

Reuse the `auth-section` / `auth-container` / `auth-card` layout from `add_expense.html` — identical structure, different title and submit label.

```html
{% extends "base.html" %}

{% block title %}Edit Expense — Spendly{% endblock %}

{% block content %}
<section class="auth-section">
  <div class="auth-container">

    <div class="auth-header">
      <h1 class="auth-title">Edit Expense</h1>
      <p class="auth-subtitle">Update the details for this transaction</p>
    </div>

    <div class="auth-card">
      {% if errors %}
      <div class="auth-error">
        {% for e in errors %}
          <div>{{ e }}</div>
        {% endfor %}
      </div>
      {% endif %}

      <form method="POST" action="{{ url_for('edit_expense', expense_id=expense.id) }}">
        <div class="form-group">
          <label for="amount">Amount ($)</label>
          <input type="number" id="amount" name="amount"
                 class="form-input" placeholder="0.00"
                 step="0.01" min="0.01"
                 value="{{ form.amount }}" required autofocus>
        </div>

        <div class="form-group">
          <label for="category">Category</label>
          <select id="category" name="category" class="form-input" required>
            {% for cat in categories %}
            <option value="{{ cat }}" {% if form.category == cat %}selected{% endif %}>{{ cat }}</option>
            {% endfor %}
          </select>
        </div>

        <div class="form-group">
          <label for="date">Date</label>
          <input type="date" id="date" name="date"
                 class="form-input"
                 value="{{ form.date }}" required>
        </div>

        <div class="form-group">
          <label for="description">
            Description <span style="color:var(--ink-faint)">(optional)</span>
          </label>
          <textarea id="description" name="description"
                    class="form-input" rows="2"
                    placeholder="e.g. Grocery shopping">{{ form.description }}</textarea>
        </div>

        <button type="submit" class="btn-submit">Save Changes</button>
      </form>
    </div>

    <p class="auth-switch">
      <a href="{{ url_for('profile') }}">← Back to profile</a>
    </p>

  </div>
</section>
{% endblock %}
```

**Template notes:**
- `action` uses `expense.id` (not `form`) — `expense` is the original DB row, always has the correct id
- Category `<select>` has no blank placeholder option — edit form always has a valid selection pre-filled
- No new CSS needed — all classes (`auth-section`, `auth-card`, `auth-error`, `form-group`, `form-input`, `btn-submit`) already defined in `style.css`

---

## Reusable patterns (no new code needed)

| Pattern | Source |
|---|---|
| `auth-section` / `auth-container` / `auth-card` layout | `templates/register.html`, `templates/add_expense.html` |
| `.form-group`, `.form-input`, `.btn-submit` styles | `static/css/style.css` |
| `.auth-error` error box | `static/css/style.css` |
| Flash messages | `templates/base.html` (auto-rendered) |
| `get_db()` + parameterised UPDATE | `database/db.py` |
| `EXPENSE_CATEGORIES` allowlist | `app.py` line 12 |
| `_date.fromisoformat()` date validation | `app.py` (already imported) |

---

## Verification

1. Start server: `python app.py`
2. Log in as demo@spendly.com / demo123
3. On `/profile`, click Edit on any expense — confirm form loads pre-filled with current values
4. Change amount to `-5` — confirm "Amount must be positive" error, form stays open
5. Clear the date field — confirm "Date is required" error
6. After validation error, confirm submitted (not original) values are shown in form
7. Submit valid edits — confirm redirect to `/profile` with success flash and updated row in table
8. Visit `/expenses/999/edit` (non-existent) — confirm redirect to `/profile` with error flash
9. Visit `/expenses/<id>/edit` while logged out — confirm redirect to `/login`
