# Plan: Delete Expense (Step 09)

## Context
Users need to remove expenses they logged by mistake. The delete flow is a two-step confirmation: `GET /expenses/<id>/delete` renders a read-only summary of the expense and asks the user to confirm. `POST /expenses/<id>/delete` executes the `DELETE` and redirects to `/profile`. Keeping mutation in POST only prevents browser prefetch and link crawlers from accidentally triggering deletions. Ownership is enforced in both queries — the `WHERE id = ? AND user_id = ?` pattern blocks IDOR.

---

## Files to modify

| File | Change |
|---|---|
| `app.py` | Implement `delete_expense` route — GET renders confirmation, POST deletes and redirects |

## Files to create

| File | Purpose |
|---|---|
| `templates/delete_expense.html` | Confirmation page showing expense details before deletion |

---

## Implementation steps

### 1. Update `app.py` — `delete_expense` route

Replace the stub at `/expenses/<int:expense_id>/delete` with the full implementation.

```python
@app.route("/expenses/<int:expense_id>/delete", methods=["GET", "POST"])
def delete_expense(expense_id):
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
        conn.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Expense deleted successfully!", "success")
        return redirect(url_for("profile"))

    # GET — render confirmation page
    conn.close()
    return render_template("delete_expense.html", expense=expense)
```

**Key design decisions:**
- `expense` fetched at top for both GET and POST — if it doesn't exist or belongs to another user, redirects immediately before rendering anything
- `DELETE` query also includes `AND user_id = ?` — double ownership check; prevents deletion even if the fetch check were somehow bypassed
- `conn.close()` called on every code path — no connection leak
- No form data to validate on POST — the only input is `expense_id` from the URL, already ownership-checked above
- No `errors` list or re-render on POST — deletion either succeeds or the ownership check already redirected

---

### 2. Create `templates/delete_expense.html`

Confirmation page: read-only expense summary + a POST form with a single danger button. No editable fields.

```html
{% extends "base.html" %}

{% block title %}Delete Expense — Spendly{% endblock %}

{% block content %}
<section class="auth-section">
  <div class="auth-container">

    <div class="auth-header">
      <h1 class="auth-title">Delete Expense</h1>
      <p class="auth-subtitle">This action cannot be undone</p>
    </div>

    <div class="auth-card">
      <div class="delete-expense-details">
        <div class="delete-detail-row">
          <span class="delete-detail-label">Amount</span>
          <span class="delete-detail-value">${{ expense.amount | currency }}</span>
        </div>
        <div class="delete-detail-row">
          <span class="delete-detail-label">Category</span>
          <span class="delete-detail-value">{{ expense.category }}</span>
        </div>
        <div class="delete-detail-row">
          <span class="delete-detail-label">Date</span>
          <span class="delete-detail-value">{{ expense.date }}</span>
        </div>
        {% if expense.description %}
        <div class="delete-detail-row">
          <span class="delete-detail-label">Description</span>
          <span class="delete-detail-value">{{ expense.description }}</span>
        </div>
        {% endif %}
      </div>

      <p class="delete-warning">
        Are you sure you want to delete this expense? This cannot be reversed.
      </p>

      <form method="POST" action="{{ url_for('delete_expense', expense_id=expense.id) }}">
        <button type="submit" class="btn-submit btn-danger-submit">Yes, Delete Expense</button>
      </form>
    </div>

    <p class="auth-switch">
      <a href="{{ url_for('profile') }}">← Cancel, go back</a>
    </p>

  </div>
</section>
{% endblock %}
```

**Template notes:**
- `expense.amount | currency` uses the custom `currency` Jinja filter registered in `app.py` at line 16 — formats `45.5` as `45.50`
- `expense.description` is shown conditionally — the column is nullable, so omit the row entirely when empty
- Form has no inputs other than the submit button — `expense_id` comes from the URL, not a hidden field
- Cancel is a plain `<a>` link, not a button inside the form — clicking it never triggers POST
- `btn-danger-submit` class needed in `style.css` — see CSS section below

---

### 3. Add `btn-danger-submit` CSS

The delete button needs a red/danger style distinct from the standard `btn-submit`. Add to `static/css/style.css`:

```css
.btn-danger-submit {
    background: var(--danger, #c0392b);
    color: #fff;
}

.btn-danger-submit:hover {
    background: var(--danger-dark, #a93226);
}
```

If `--danger` is already defined as a CSS variable in `style.css`, reference it. If not, add it to the `:root` block:

```css
:root {
    /* existing variables... */
    --danger: #c0392b;
    --danger-dark: #a93226;
}
```

Check `style.css` for existing danger/red variables before adding new ones — use what's already there.

---

## Reusable patterns (no new code needed)

| Pattern | Source |
|---|---|
| `auth-section` / `auth-container` / `auth-card` layout | `templates/register.html`, `templates/add_expense.html` |
| `.btn-submit` base button styles | `static/css/style.css` |
| Flash messages | `templates/base.html` (auto-rendered) |
| `get_db()` + parameterised DELETE | `database/db.py` |
| `currency` Jinja filter | `app.py` line 16 — `@app.template_filter('currency')` |
| Ownership-check pattern (`WHERE id = ? AND user_id = ?`) | `app.py` `edit_expense` route |

---

## Verification

1. Start server: `python app.py`
2. Log in as demo@spendly.com / demo123
3. On `/profile`, click Delete on any expense — confirm confirmation page loads with correct amount, category, date, description
4. Confirm amount is formatted (e.g. `$45.50` not `45.5`)
5. Click "← Cancel, go back" — confirm redirect to `/profile` with no deletion
6. Repeat step 3, click "Yes, Delete Expense" — confirm redirect to `/profile` with success flash
7. Confirm deleted expense no longer appears in the expenses table
8. Visit `/expenses/999/delete` (non-existent) — confirm redirect to `/profile` with error flash
9. Visit `/expenses/<id>/delete` while logged out — confirm redirect to `/login`
10. Confirm `GET /expenses/<id>/delete` does not delete anything — only POST mutates
