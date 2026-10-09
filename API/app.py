"""Expense Tracker API - one endpoint per query in sql/queries.sql."""
import hmac
import os
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask.json.provider import DefaultJSONProvider
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from psycopg.rows import dict_row

load_dotenv(Path(__file__).parent / ".env")


class JSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(o):
        if isinstance(o, date):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


app = Flask(__name__)
app.json = JSONProvider(app)
app.secret_key = os.environ["SECRET_KEY"]

DB = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
}


def run(sql, params=()):
    """Run one statement; return rows if it produces any, else the row count."""
    with psycopg.connect(**DB, row_factory=dict_row) as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall() if cur.description else cur.rowcount


def bad_request(message, status=400):
    return jsonify(error=message), status


# --- Auth: a single user whose credentials live in .env ---------------------

login_manager = LoginManager(app)


class User(UserMixin):
    id = os.environ["API_USERNAME"]


@login_manager.user_loader
def load_user(user_id):
    return User() if user_id == User.id else None


@login_manager.unauthorized_handler
def unauthorized():
    return bad_request("login required", 401)


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", ""))
    password = str(data.get("password", ""))
    valid = hmac.compare_digest(username.encode(), User.id.encode()) and hmac.compare_digest(
        password.encode(), os.environ["API_PASSWORD"].encode()
    )
    if not valid:
        return bad_request("invalid credentials", 401)
    login_user(User())
    return jsonify(message="logged in")


@app.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(message="logged out")


# --- Database errors -> JSON responses --------------------------------------

@app.errorhandler(psycopg.errors.UniqueViolation)
def handle_unique(e):
    return bad_request("already exists", 409)


@app.errorhandler(psycopg.errors.IntegrityError)
@app.errorhandler(psycopg.errors.DataError)
def handle_invalid(e):
    return bad_request(e.diag.message_primary or "invalid input")


@app.errorhandler(psycopg.OperationalError)
def handle_unavailable(e):
    return bad_request("database unavailable", 503)


# --- Use Case 1: add a new expense category ---------------------------------

@app.post("/categories")
@login_required
def add_category():
    data = request.get_json(silent=True) or {}
    if not data.get("name"):
        return bad_request("name is required")
    rows = run("INSERT INTO categories (name) VALUES (%s) RETURNING id, name", (data["name"],))
    return jsonify(rows[0]), 201


# --- Use Case 2: view all categories ----------------------------------------

@app.get("/categories")
@login_required
def list_categories():
    return jsonify(run("SELECT id, name FROM categories ORDER BY name"))


# --- Use Case 3: add a new expense ------------------------------------------

@app.post("/expenses")
@login_required
def add_expense():
    data = request.get_json(silent=True) or {}
    fields = ("category_id", "amount", "description", "date")
    missing = [f for f in fields if data.get(f) in (None, "")]
    if missing:
        return bad_request(f"missing fields: {', '.join(missing)}")
    rows = run(
        """
        INSERT INTO expenses (category_id, amount, description, date)
        VALUES (%s, %s, %s, %s)
        RETURNING id, category_id, amount, description, date
        """,
        [data[f] for f in fields],
    )
    return jsonify(rows[0]), 201


# --- Use Case 4: view all expenses (most recent first) ----------------------

@app.get("/expenses")
@login_required
def list_expenses():
    return jsonify(run(
        """
        SELECT e.id, c.name AS category, e.amount, e.description, e.date
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.date DESC
        """
    ))


# --- Use Case 5: view all expenses for a specific category ------------------

@app.get("/expenses/by-category")
@login_required
def expenses_by_category():
    name = request.args.get("name")
    if not name:
        return bad_request("name query parameter is required")
    return jsonify(run(
        """
        SELECT e.id, e.amount, e.description, e.date
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE c.name = %s
        ORDER BY e.date DESC
        """,
        (name,),
    ))


# --- Use Case 6: total spending per category --------------------------------

@app.get("/expenses/totals-by-category")
@login_required
def totals_by_category():
    return jsonify(run(
        """
        SELECT c.name AS category, COUNT(e.id) AS num_expenses, SUM(e.amount) AS total_spent
        FROM categories c
        LEFT JOIN expenses e ON c.id = e.category_id
        GROUP BY c.id, c.name
        ORDER BY total_spent DESC NULLS LAST
        """
    ))


# --- Use Case 7: view expenses within a date range --------------------------

@app.get("/expenses/by-date-range")
@login_required
def expenses_by_date_range():
    start, end = request.args.get("start"), request.args.get("end")
    if not start or not end:
        return bad_request("start and end query parameters are required (YYYY-MM-DD)")
    return jsonify(run(
        """
        SELECT e.id, c.name AS category, e.amount, e.description, e.date
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.date BETWEEN %s AND %s
        ORDER BY e.date DESC
        """,
        (start, end),
    ))


# --- Use Case 8: total spending for a given month ---------------------------

@app.get("/expenses/monthly-total")
@login_required
def monthly_total():
    month = request.args.get("month")
    if not month:
        return bad_request("month query parameter is required (YYYY-MM)")
    rows = run(
        "SELECT SUM(amount) AS monthly_total FROM expenses WHERE to_char(date, 'YYYY-MM') = %s",
        (month,),
    )
    return jsonify(rows[0])


# --- Use Case 9: delete an expense ------------------------------------------

@app.delete("/expenses/<int:expense_id>")
@login_required
def delete_expense(expense_id):
    if not run("DELETE FROM expenses WHERE id = %s", (expense_id,)):
        return bad_request("expense not found", 404)
    return "", 204


if __name__ == "__main__":
    app.run(host=os.environ["API_HOST"], port=int(os.environ["API_PORT"]))
