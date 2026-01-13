from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path("library.db")

# -------------------- DB Helpers -------------------- #
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                isbn TEXT,
                category TEXT,
                year INTEGER,
                available INTEGER DEFAULT 1
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                status TEXT DEFAULT 'Active'
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book TEXT,
                member TEXT,
                type TEXT,
                date TEXT,
                dueDate TEXT,
                status TEXT,
                condition TEXT
            );
        """)
        conn.commit()

# -------------------- Routes -------------------- #
@app.route("/")
def home():
    return render_template("LibraryManagement.html")

# ---------- Books API ---------- #
@app.route("/api/books", methods=["GET"])
def get_books():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM books").fetchall()
        return jsonify([dict(r) for r in rows])

@app.route("/api/books", methods=["POST"])
def add_book():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO books (title, author, isbn, category, year, available)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data["title"], data["author"], data["isbn"], data["category"], data["year"], int(data.get("available", 1))))
        conn.commit()
    return jsonify({"message": "Book added"}), 201

@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def delete_book(book_id):
    with get_db() as conn:
        conn.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
    return jsonify({"message": "Book deleted"})

# ---------- Members API ---------- #
@app.route("/api/members", methods=["GET"])
def get_members():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM members").fetchall()
        return jsonify([dict(r) for r in rows])

@app.route("/api/members", methods=["POST"])
def add_member():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO members (name, email, phone, address, status)
            VALUES (?, ?, ?, ?, ?)
        """, (data["name"], data["email"], data["phone"], data["address"], "Active"))
        conn.commit()
    return jsonify({"message": "Member added"}), 201

@app.route("/api/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    with get_db() as conn:
        conn.execute("DELETE FROM members WHERE id=?", (member_id,))
        conn.commit()
    return jsonify({"message": "Member deleted"})

# ---------- Transactions API ---------- #
@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM transactions").fetchall()
        return jsonify([dict(r) for r in rows])

@app.route("/api/transactions", methods=["POST"])
def add_transaction():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO transactions (book, member, type, date, dueDate, status, condition)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (data.get("book"), data.get("member"), data.get("type"), data.get("date"),
              data.get("dueDate"), data.get("status"), data.get("condition")))
        # if borrow → mark book unavailable
        if data.get("type") == "Borrow":
            conn.execute("UPDATE books SET available=0 WHERE title=?", (data.get("book"),))
        if data.get("type") == "Return":
            conn.execute("UPDATE books SET available=1 WHERE title=?", (data.get("book"),))
        conn.commit()
    return jsonify({"message": "Transaction added"}), 201

# -------------------- Main -------------------- #
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
