from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db, init_db, seed_db, get_expenses_for_user, summarise_expenses
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date as _date
import csv
import os
from io import StringIO

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

# Custom filter for currency formatting
@app.template_filter('currency')
def currency_filter(value):
    try:
        amount = float(value)
        return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

with app.app_context():
    init_db()
    seed_db()

# Routes
@app.route("/")
def landing():
    if "user_id" in session:
        return redirect(url_for("profile"))
    return render_template("landing.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # Prevent logged-in users from accessing register page
    if "user_id" in session:
        flash("You are already logged in", "info")
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not name:
            errors.append("Name is required")
        if not email:
            errors.append("Email is required")
        elif "@" not in email or "." not in email.split("@")[1] if "@" in email else True:
            errors.append("Invalid email format")
        if not password:
            errors.append("Password is required")
        elif len(password) < 8:
            errors.append("Password must be at least 8 characters")
        confirm_password = request.form.get("confirm_password", "").strip()
        if not confirm_password:
            errors.append("Confirm password is required")
        elif password != confirm_password:
            errors.append("Passwords do not match")

        if errors:
            return render_template("register.html", error="; ".join(errors))

        conn = get_db()
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", error="Email already registered")

        password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except Exception as e:
            conn.close()
            return render_template("register.html", error="Registration failed. Please try again.")

    return render_template("register.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        flash("You are already logged in", "info")
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        errors = []
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")
        if errors:
            return render_template("login.html", error="; ".join(errors))

        conn = get_db()
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Logged in successfully!", "success")
            return redirect(url_for("landing"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")

@app.route("/logout")
def logout():
    if "user_id" not in session:
        flash("You are already logged out", "info")
        return redirect(url_for("landing"))

    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("landing"))

# Expense routes
@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Amount must be positive")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")

        if not category:
            errors.append("Category is required")
        if not date:
            errors.append("Date is required")

        if errors:
            flash("; ".join(errors), "error")
            return redirect(url_for("profile"))

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], amount, category, date, description)
        )
        conn.commit()
        conn.close()

        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    return redirect(url_for("profile"))

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
        amount = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        try:
            amount = float(amount)
            if amount <= 0:
                errors.append("Amount must be positive")
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number")

        if not category:
            errors.append("Category is required")
        if not date:
            errors.append("Date is required")

        if errors:
            flash("; ".join(errors), "error")
            return redirect(url_for("profile"))

        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?",
            (amount, category, date, description, expense_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Expense updated successfully!", "success")
        return redirect(url_for("profile"))

    conn.close()
    return render_template("edit_expense.html", expense=expense)

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

    conn.close()
    return render_template("delete_expense.html", expense=expense)

# Profile Routes
@app.route("/profile")
def profile():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    try:
        if start_date:
            _date.fromisoformat(start_date)
        if end_date:
            _date.fromisoformat(end_date)
        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date after end_date")
    except ValueError:
        flash("Invalid date filter — showing all expenses.", "error")
        start_date = end_date = None

    conn = get_db()
    user = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    expenses = get_expenses_for_user(conn, session["user_id"], start_date, end_date)
    conn.close()

    total_spent, average, top_category, category_breakdown = summarise_expenses(expenses)

    # When a filter is active show all matching expenses;
    # otherwise cap the table to the most recent 10.
    filter_active = bool(start_date or end_date)
    recent_expenses = expenses if filter_active else expenses[:10]

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        recent_expenses=recent_expenses,
        filter_active=filter_active,
        total_spent=total_spent,
        total_spent_formatted=f"{total_spent:.2f}",
        average=round(average, 2),
        top_category_name=top_category[0],
        top_category_amount=top_category[1],
        category_breakdown=category_breakdown,
        start_date=start_date or "",
        end_date=end_date or "",
    )
    
@app.route("/profile/export")
def export_expenses():
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    expenses = conn.execute(
        "SELECT category, amount, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Category", "Amount", "Date", "Description"])
    for e in expenses:
        writer.writerow([e["category"], e["amount"], e["date"], e["description"]])

    csv_data = output.getvalue()
    output.close()

    return csv_data, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=expenses.csv"
    }

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=5001)