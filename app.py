from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash

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


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # Prevent logged-in users from accessing register page
    if "user_id" in session:
        flash("You are already logged in", "info")
        return redirect(url_for("landing"))

    if request.method == "POST":
        # Get form data
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validation
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

        # Check if email already exists
        conn = get_db()
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_user:
            conn.close()
            return render_template("register.html", error="Email already registered")

        # Hash password
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        # Insert new user using parameterized query (no SQL injection)
        try:
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            conn.commit()
            conn.close()

            # Redirect to login after successful registration
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


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/login", methods=["GET", "POST"])
def login():
    # Prevent logged-in users from accessing login page
    if "user_id" in session:
        flash("You are already logged in", "info")
        return redirect(url_for("landing"))

    if request.method == "POST":
        # Get form data
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        # Validation
        errors = []
        if not email:
            errors.append("Email is required")
        if not password:
            errors.append("Password is required")

        if errors:
            return render_template("login.html", error="; ".join(errors))

        # Check user credentials
        conn = get_db()
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            # Login successful - store user id in session
            session["user_id"] = user["id"]
            flash("Logged in successfully!", "success")
            return redirect(url_for("landing"))
        else:
            # Invalid credentials
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


@app.route("/logout")
def logout():
    # Prevent logged-out users from accessing logout page
    if "user_id" not in session:
        flash("You are already logged out", "info")
        return redirect(url_for("landing"))

    # Clear session
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for("landing"))




@app.route("/expenses/add")
def add_expense():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))
    return "Delete expense — coming in Step 9"
@app.route("/profile")
def profile():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    # Hardcoded user data for UI design
    user = {
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "member_since": "Jan 2023"
    }

    # Hardcoded expense data for UI design
    expenses = [
        {"date": "2026-04-10", "description": "Grocery Store", "category": "Food", "amount": 45.30},
        {"date": "2026-04-08", "description": "Uber Ride", "category": "Transport", "amount": 12.50},
        {"date": "2026-04-05", "description": "Electricity Bill", "category": "Bills", "amount": 89.99},
        {"date": "2026-04-03", "description": "Restaurant Dinner", "category": "Food", "amount": 67.00},
        {"date": "2026-04-01", "description": "Monthly Gym", "category": "Health", "amount": 35.00},
        {"date": "2026-03-28", "description": "Online Books", "category": "Shopping", "amount": 28.75},
        {"date": "2026-03-25", "description": "Bus Pass", "category": "Transport", "amount": 65.00}
    ]

    total_spent = sum(float(e["amount"]) for e in expenses)
    total_spent_formatted = f"{total_spent:.2f}"
    average = total_spent / len(expenses) if expenses else 0
    average_formatted = f"{average:.2f}"

    # Calculate top category
    from collections import Counter
    category_totals = Counter()
    for e in expenses:
        category_totals[e["category"]] += float(e["amount"])

    if category_totals:
        top_category_entry = category_totals.most_common(1)[0]
        top_category_name = top_category_entry[0]
        top_category_amount = top_category_entry[1]
    else:
        top_category_name = "None"
        top_category_amount = 0

    top_category_formatted = f"{top_category_amount:.2f}"

    # Recent expenses for the table
    recent_expenses = expenses[:5]

    # Category breakdown for progress bars
    category_breakdown = []
    total_for_percent = total_spent if total_spent > 0 else 1
    for cat, amt in category_totals.most_common():
        category_breakdown.append({
            "name": cat,
            "amount": amt,
            "percentage": round((amt / total_for_percent) * 100, 1)
        })

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        recent_expenses=recent_expenses,
        total_spent=total_spent,
        total_spent_formatted=total_spent_formatted,
        average=round(average, 2),
        average_formatted=average_formatted,
        top_category_name=top_category_name,
        category_breakdown=category_breakdown
    )
@app.route("/profile/expenses")
def profile_expenses():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))


@app.route("/profile/export")
def export_expenses():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))

    conn = get_db()
    expenses = conn.execute(
        "SELECT category, amount, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    # Generate CSV
    import csv
    from io import StringIO
    
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
    app.run(debug=True, port=5001)