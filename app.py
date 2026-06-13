from flask import Flask, render_template, request, redirect, session, send_file
from openpyxl import Workbook
import sqlite3


app = Flask(__name__)

app.secret_key = "asset_management_secret"


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("assets.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/")

        return "Invalid Username or Password"

    return render_template("login.html")


# LOGOUT
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# HOME
@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search", "")

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    if search:

        cursor.execute("""
            SELECT * FROM assets
            WHERE asset_name LIKE ?
            OR asset_type LIKE ?
            OR serial_number LIKE ?
        """, (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

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
        JOIN assets
        ON assignments.asset_id = assets.id
        JOIN employees
        ON assignments.employee_id = employees.id
        ORDER BY assignments.id DESC
    """)

    assignments = cursor.fetchall()

    total_assets = len(assets)

    available_assets = len(
        [a for a in assets if a[4] == "Available"]
    )

    assigned_assets = len(
        [a for a in assets if a[4] == "Assigned"]
    )

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


# ADD ASSET
@app.route("/add", methods=["POST"])
def add_asset():

    asset_name = request.form["asset_name"]
    asset_type = request.form["asset_type"]
    serial_number = request.form["serial_number"]

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO assets
        (asset_name, asset_type, serial_number, status)
        VALUES (?, ?, ?, ?)
    """, (
        asset_name,
        asset_type,
        serial_number,
        "Available"
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# EDIT ASSET
@app.route("/edit_asset/<int:asset_id>", methods=["GET", "POST"])
def edit_asset(asset_id):

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    if request.method == "POST":

        asset_name = request.form["asset_name"]
        asset_type = request.form["asset_type"]
        serial_number = request.form["serial_number"]
        status = request.form["status"]

        cursor.execute("""
            UPDATE assets
            SET asset_name=?,
                asset_type=?,
                serial_number=?,
                status=?
            WHERE id=?
        """, (
            asset_name,
            asset_type,
            serial_number,
            status,
            asset_id
        ))

        conn.commit()
        conn.close()

        return redirect("/")

    cursor.execute(
        "SELECT * FROM assets WHERE id=?",
        (asset_id,)
    )

    asset = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_asset.html",
        asset=asset
    )


# DELETE ASSET
@app.route("/delete_asset/<int:asset_id>")
def delete_asset(asset_id):

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM assets WHERE id=?",
        (asset_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# ADD EMPLOYEE
@app.route("/add_employee", methods=["POST"])
def add_employee():

    employee_name = request.form["employee_name"]
    department = request.form["department"]

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO employees
        (employee_name, department)
        VALUES (?, ?)
    """, (
        employee_name,
        department
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# ASSIGN ASSET
@app.route("/assign_asset", methods=["POST"])
def assign_asset():

    asset_id = request.form["asset_id"]
    employee_id = request.form["employee_id"]

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO assignments
        (asset_id, employee_id)
        VALUES (?, ?)
    """, (
        asset_id,
        employee_id
    ))

    cursor.execute("""
        UPDATE assets
        SET status='Assigned'
        WHERE id=?
    """, (asset_id,))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/export_assets")
def export_assets():

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM assets")
    assets = cursor.fetchall()

    conn.close()

    wb = Workbook()
    ws = wb.active

    ws.title = "Assets"

    ws.append([
        "ID",
        "Asset Name",
        "Asset Type",
        "Serial Number",
        "Status"
    ])

    for asset in assets:
        ws.append(asset)

    wb.save("assets_report.xlsx")

    return send_file(
        "assets_report.xlsx",
        as_attachment=True
    )

@app.route("/export_employees")
def export_employees():

    conn = sqlite3.connect("assets.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees")
    employees = cursor.fetchall()

    conn.close()

    wb = Workbook()
    ws = wb.active

    ws.title = "Employees"

    ws.append([
        "ID",
        "Employee Name",
        "Department"
    ])

    for employee in employees:
        ws.append(employee)

    wb.save("employees_report.xlsx")

    return send_file(
        "employees_report.xlsx",
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)