from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_file
)

from openpyxl import Workbook
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

import sqlite3
import os

app = Flask(__name__)

# =========================
# SECRET KEY (SECURE)
# =========================
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")


# =========================
# DATABASE CONNECTION
# =========================
def get_db_connection():
    conn = sqlite3.connect("assets.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# LOGIN DECORATOR
# =========================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# =========================
# CREATE TABLES
# =========================
def create_tables():
    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        asset_type TEXT,
        serial_number TEXT UNIQUE,
        status TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_name TEXT,
        department TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        employee_id INTEGER,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Default admin
    hashed_password = generate_password_hash("admin123")

    cursor.execute("""
    INSERT OR IGNORE INTO users (id, username, password)
    VALUES (?, ?, ?)
    """, (1, "admin", hashed_password))

    conn.commit()
    conn.close()


create_tables()


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            return redirect("/")

        return "Invalid Username or Password"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# HOME
# =========================
@app.route("/")
@login_required
def home():
    search = request.args.get("search", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM assets
            WHERE asset_name LIKE ?
            OR asset_type LIKE ?
            OR serial_number LIKE ?
        """, (f"%{search}%", f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM assets")

    assets = cursor.fetchall()

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()

    cursor.execute("""
        SELECT assignments.id,
               assets.asset_name,
               employees.employee_name,
               assignments.assigned_date
        FROM assignments
        JOIN assets ON assignments.asset_id = assets.id
        JOIN employees ON assignments.employee_id = employees.id
        ORDER BY assignments.id DESC
    """)
    assignments = cursor.fetchall()

    total_assets = len(assets)
    available_assets = len([a for a in assets if a["status"] == "Available"])
    assigned_assets = len([a for a in assets if a["status"] == "Assigned"])

    conn.close()

    return render_template(
        "index.html",
        assets=assets,
        employees=employees,
        assignments=assignments,
        total_assets=total_assets,
        available_assets=available_assets,
        assigned_assets=assigned_assets,
        search=search
    )


# =========================
# ADD ASSET
# =========================
@app.route("/add", methods=["POST"])
@login_required
def add_asset():
    asset_name = request.form["asset_name"]
    asset_type = request.form["asset_type"]
    serial_number = request.form["serial_number"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assets WHERE serial_number=?", (serial_number,))
    if cursor.fetchone():
        conn.close()
        return "Serial Number Already Exists"

    cursor.execute("""
        INSERT INTO assets (asset_name, asset_type, serial_number, status)
        VALUES (?, ?, ?, ?)
    """, (asset_name, asset_type, serial_number, "Available"))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# EDIT ASSET
# =========================
@app.route("/edit_asset/<int:asset_id>", methods=["GET", "POST"])
@login_required
def edit_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        asset_name = request.form["asset_name"]
        asset_type = request.form["asset_type"]
        serial_number = request.form["serial_number"]
        status = request.form["status"]

        # CHECK DUPLICATE SERIAL (IMPORTANT FIX)
        cursor.execute("""
            SELECT id FROM assets
            WHERE serial_number=? AND id!=?
        """, (serial_number, asset_id))

        if cursor.fetchone():
            conn.close()
            return "Serial Number Already Exists"

        cursor.execute("""
            UPDATE assets
            SET asset_name=?,
                asset_type=?,
                serial_number=?,
                status=?
            WHERE id=?
        """, (asset_name, asset_type, serial_number, status, asset_id))

        conn.commit()
        conn.close()
        return redirect("/")

    cursor.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
    asset = cursor.fetchone()

    conn.close()
    return render_template("edit_asset.html", asset=asset)


# =========================
# DELETE ASSET
# =========================
@app.route("/delete_asset/<int:asset_id>")
@login_required
def delete_asset(asset_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM assignments WHERE asset_id=?", (asset_id,))
    cursor.execute("DELETE FROM assets WHERE id=?", (asset_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# ADD EMPLOYEE
# =========================
@app.route("/add_employee", methods=["POST"])
@login_required
def add_employee():
    employee_name = request.form["employee_name"]
    department = request.form["department"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO employees (employee_name, department)
        VALUES (?, ?)
    """, (employee_name, department))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# ASSIGN ASSET
# =========================
@app.route("/assign_asset", methods=["POST"])
@login_required
def assign_asset():
    asset_id = request.form["asset_id"]
    employee_id = request.form["employee_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assets WHERE id=?", (asset_id,))
    asset = cursor.fetchone()

    if not asset:
        conn.close()
        return "Asset Not Found"

    if asset["status"] == "Assigned":
        conn.close()
        return "Asset Already Assigned"

    cursor.execute("""
        INSERT INTO assignments (asset_id, employee_id)
        VALUES (?, ?)
    """, (asset_id, employee_id))

    cursor.execute("""
        UPDATE assets
        SET status='Assigned'
        WHERE id=?
    """, (asset_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# RETURN ASSET
# =========================
@app.route("/return_asset/<int:assignment_id>")
@login_required
def return_asset(assignment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT asset_id FROM assignments WHERE id=?", (assignment_id,))
    assignment = cursor.fetchone()

    if assignment:
        asset_id = assignment["asset_id"]

        cursor.execute("""
            UPDATE assets
            SET status='Available'
            WHERE id=?
        """, (asset_id,))

        cursor.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))

        conn.commit()

    conn.close()
    return redirect("/")


# =========================
# EXPORT ASSETS
# =========================
@app.route("/export_assets")
@login_required
def export_assets():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assets")
    assets = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Assets"

    ws.append(["ID", "Asset Name", "Asset Type", "Serial Number", "Status"])

    for a in assets:
        ws.append([a["id"], a["asset_name"], a["asset_type"], a["serial_number"], a["status"]])

    filename = "assets_report.xlsx"
    wb.save(filename)

    return send_file(filename, as_attachment=True)


# =========================
# EXPORT EMPLOYEES
# =========================
@app.route("/export_employees")
@login_required
def export_employees():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Employees"

    ws.append(["ID", "Employee Name", "Department"])

    for e in employees:
        ws.append([e["id"], e["employee_name"], e["department"]])

    filename = "employees_report.xlsx"
    wb.save(filename)

    return send_file(filename, as_attachment=True)


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)