import random
import string
from datetime import datetime
from werkzeug.security import generate_password_hash
from database.db import get_db

# Sample Indian first and last names
FIRST_NAMES = [
    "Aarav", "Vihaan", "Ishaan", "Aditya", "Rohan", "Arjun", "Krishna", "Rahul",
    "Aditi", "Priya", "Sanjana", "Ananya", "Deepika", "Neha", "Kavya", "Isha",
    "Rohit", "Manish", "Sanjay", "Vikram"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Kumar", "Gupta", "Mehta", "Reddy", "Nair",
    "Joshi", "Verma", "Chopra", "Bhatia", "Desai", "Ghosh", "Roy", "Mishra"
]

def generate_name():
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"

def generate_email(name: str):
    # create email like first.lastNN@example.com
    first, last = name.lower().split()
    suffix = "".join(random.choices(string.digits, k=random.choice([2, 3])))
    return f"{first}.{last}{suffix}@gmail.com"

def main():
    conn = get_db()
    cursor = conn.cursor()
    while True:
        name = generate_name()
        email = generate_email(name)
        # Check uniqueness
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            break
    password_hash = generate_password_hash("password123", method="pbkdf2:sha256")
    created_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, created_at),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"Inserted user: id={user_id}, name={name}, email={email}")

if __name__ == "__main__":
    main()
