from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "super-secret-key"  

DB_PATH = Path("bank.db")

# ---------------- DB Helpers ---------------- #

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                pin_hash TEXT NOT NULL,
                age INTEGER,
                account_number TEXT NOT NULL,
                branch TEXT
            );
        """)
        # Transactions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT CHECK(type IN ('deposit','withdrawal')) NOT NULL,
                amount REAL NOT NULL,
                label TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
        """)
        conn.commit()

# ---------------- Routes ---------------- #

@app.route("/")
def home():
    return render_template("sign_up.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    pin = request.form["pin"]
    cpin = request.form["cpin"]
    age = request.form.get("age")
    account_number = request.form.get("account_number")
    branch = request.form.get("branch")

    if pin != cpin:
        return "❌ PINs do not match"

    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO users (name, pin_hash, age, account_number, branch)
                VALUES (?, ?, ?, ?, ?)
            """, (name, generate_password_hash(pin), age, account_number, branch))
            conn.commit()
    except sqlite3.IntegrityError:
        return "❌ Account number already exists. Please choose another."

    return redirect(url_for("signin"))

@app.route("/signin")
def signin():
    return render_template("sign_in.html")

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    pin = request.form["pin"]

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()

    if user and check_password_hash(user["pin_hash"], pin):
        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))
    else:
        return "❌ Invalid credentials"

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    uid = session["user_id"]

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        txns = conn.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()

    # calculate balance
    balance = 0
    for t in txns:
        if t["type"] == "deposit":
            balance += t["amount"]
        else:
            balance -= t["amount"]

    return render_template("dashboard.html", user=user, transactions=txns, balance=balance)

@app.route("/txn/deposit", methods=["POST"])
def deposit():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    amount = float(request.form["amount"])
    label = request.form.get("label", "Deposit")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO transactions (user_id, type, amount, label)
            VALUES (?, 'deposit', ?, ?)
        """, (session["user_id"], amount, label))
        conn.commit()

    return redirect(url_for("dashboard"))

@app.route("/txn/withdraw", methods=["POST"])
def withdraw():
    if "user_id" not in session:
        return redirect(url_for("signin"))

    amount = float(request.form["amount"])
    label = request.form.get("label", "Withdraw")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO transactions (user_id, type, amount, label)
            VALUES (?, 'withdrawal', ?, ?)
        """, (session["user_id"], amount, label))
        conn.commit()

    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))

# ---------------- Main ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
