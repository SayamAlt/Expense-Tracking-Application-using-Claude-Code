from flask import Flask, render_template, request, redirect, url_for, session, flash
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

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


@app.route("/profile")
def profile():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to access this page", "warning")
        return redirect(url_for("login"))
    return "Profile page — User ID: " + str(session["user_id"])


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


if __name__ == "__main__":
    app.run(debug=True, port=5001)