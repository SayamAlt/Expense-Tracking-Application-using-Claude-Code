from flask import Flask, render_template, request, redirect, url_for
from database.db import get_db, init_db, seed_db
from werkzeug.security import generate_password_hash

app = Flask(__name__)

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


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)