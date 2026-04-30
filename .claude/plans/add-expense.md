# Plan: Add Expense (Step 07)

## Context
Users currently have no UI to add an expense. `GET /expenses/add` just redirects to `/profile`, and there's no form anywhere on the profile page. The POST handling in `app.py` is partially written but has two problems: on validation failure it flashes and redirects (losing form state) instead of re-rendering the form with errors, and the GET handler never renders a form at all. This step wires up the full add-expense flow: a dedicated page with a form, server-side validation that re-renders on failure, and a button on the profile page to reach it.

---

## Files to modify

| File | Change |
|---|---|
| `app.py` | Fix GET to render template; fix POST to re-render on errors |
| `templates/profile.html` | Add "Add Expense" button in the section header |

## Files to create

| File | Purpose |
|---|---|
| `templates/add_expense.html` | Dedicated add-expense form page |

---

## Implementation steps

### 1. Update `app.py` — `add_expense` route

**Current GET** (line 180): `return redirect(url_for("profile"))`
**Fix**: Render the template, passing today's date as default.

```python
from datetime import date as _date   # already imported

@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    categories = ["Food", "Transport", "Bills", "Health",
                  "Entertainment", "Shopping", "Other"]

    if request.method == "POST":
        amount_raw   = request.form.get("amount", "").strip()
        category     = request.form.get("category", "").strip()
        date         = request.form.get("date", "").strip()
        description  = request.form.get("description", "").strip()

        errors = []
        amount = None
        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be positive")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")

        if not category or category not in categories:
            errors.append("Please select a valid category")
        if not date:
            errors.append("Date is required")

        if errors:
            # Re-render form — do NOT redirect, preserve entered values
            return render_template(
                "add_expense.html",
                errors=errors,
                categories=categories,
                form={"amount": amount_raw, "category": category,
                      "date": date, "description": description},
            )

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description)"
            " VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, date, description),
        )
        conn.commit()
        conn.close()

        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    # GET
    return render_template(
        "add_expense.html",
        errors=[],
        categories=categories,
        form={"amount": "", "category": "", "date": _date.today().isoformat(),
              "description": ""},
    )
```

**Key changes vs current code:**
- GET renders `add_expense.html` instead of redirecting
- POST on error re-renders the form (not flash+redirect) with `errors` list and pre-filled `form` dict
- Category validated server-side against the allowed list
- `_date` already imported at line 4 — no new imports needed

---

### 2. Create `templates/add_expense.html`

Reuse the `auth-section` / `auth-container` / `auth-card` pattern from `register.html` — already styled, no new CSS needed.

```html
{% extends "base.html" %}

{% block title %}Add Expense — Spendly{% endblock %}

{% block content %}
<section class="auth-section">
  <div class="auth-container">

    <div class="auth-header">
      <h1 class="auth-title">Add Expense</h1>
      <p class="auth-subtitle">Log a new transaction to your account</p>
    </div>

    <div class="auth-card">
      {% if errors %}
      <div class="auth-error">
        {% for e in errors %}
          <div>{{ e }}</div>
        {% endfor %}
      </div>
      {% endif %}

      <form method="POST" action="{{ url_for('add_expense') }}">
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
            <option value="" disabled {% if not form.category %}selected{% endif %}>
              Select a category
            </option>
            {% for cat in categories %}
            <option value="{{ cat }}"
              {% if form.category == cat %}selected{% endif %}>
              {{ cat }}
            </option>
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
          <label for="description">Description <span style="color:var(--ink-faint)">(optional)</span></label>
          <textarea id="description" name="description"
                    class="form-input" rows="2"
                    placeholder="e.g. Grocery shopping">{{ form.description }}</textarea>
        </div>

        <button type="submit" class="btn-submit">Add Expense</button>
      </form>
    </div>

    <p class="auth-switch">
      <a href="{{ url_for('profile') }}">← Back to profile</a>
    </p>

  </div>
</section>
{% endblock %}
```

**CSS note:** `form-input` already styles `<select>` and `<textarea>` identically to `<input>` — no page-specific CSS file needed.

---

### 3. Modify `templates/profile.html` — add "Add Expense" button

In the `section-header` div of the "Recent Expenses" section, add the button alongside the title:

**Change** `<div class="section-header">` to:
```html
<div class="section-header" style="display:flex; align-items:center; justify-content:space-between;">
```
And after the closing `</h2>` tag, add:
```html
  <a href="{{ url_for('add_expense') }}" class="btn-primary" style="font-size:0.82rem; padding:0.4rem 1rem;">
    + Add Expense
  </a>
```

This keeps the change minimal — reuses `btn-primary` (already defined in `style.css`) with small inline overrides for compact size. No new CSS needed.

---

## Reusable patterns (no new code needed)

| Pattern | Source |
|---|---|
| `auth-section` / `auth-container` / `auth-card` layout | `templates/register.html` |
| `.form-group`, `.form-input`, `.btn-submit` styles | `static/css/style.css` |
| `.auth-error` error box | `static/css/style.css` |
| `.btn-primary` button | `static/css/style.css` |
| Flash messages | `templates/base.html` (auto-rendered) |
| `get_db()` + parameterised INSERT | `database/db.py` |
| `_date` import | `app.py` line 4 (already present) |

---

## Verification

1. Start the server: `python app.py`
2. Log in as demo@spendly.com / demo123
3. Visit `/profile` — confirm "+ Add Expense" button appears in the Recent Expenses header
4. Click it — confirm `/expenses/add` renders the form with today's date pre-filled
5. Submit empty form — confirm errors appear inline, form values preserved
6. Submit amount=`-5` — confirm "Amount must be positive" error
7. Submit a valid expense (e.g. $20, Food, today, "Lunch") — confirm redirect to `/profile` with success flash and new row in the table
8. Visit `/expenses/add` while logged out — confirm redirect to `/login`
