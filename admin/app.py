from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "users.db"))

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Чтобы обращаться к полям по имени
    return conn

@app.route("/")
def index():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users ORDER BY end_date DESC").fetchall()
    conn.close()
    return render_template("index.html", users=users)

@app.route("/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    if request.method == "POST":
        email = request.form["email"]
        fullname = request.form["fullname"]
        phone = request.form["phone"]
        city = request.form["city"]

        conn.execute("""
            UPDATE users
            SET email = ?, fullname = ?, phone = ?, city = ?
            WHERE user_id = ?
        """, (email, fullname, phone, city, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    conn.close()
    return render_template("edit.html", user=user)

@app.route("/delete/<int:user_id>")
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)