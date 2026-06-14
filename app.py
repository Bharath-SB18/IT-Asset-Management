from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_file
)

from openpyxl import Workbook

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import sqlite3
import os

app = Flask(__name__)

app.secret_key = "asset_management_secret"


# DATABASE CONNECTION

def get_db_connection():

    conn = sqlite3.connect("assets.db")

    conn.row_factory = sqlite3.Row

    return conn


# LOGIN CHECK

def login_required():

    if "user" not in session:
        return False

    return True


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # GET USER

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        # CHECK HASHED PASSWORD

        if user and check_password_hash(
            user["password"],
            password
        ):

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

    if not login_required():
        return redirect("/login")

    search = request.args.get("search", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    # SEARCH ASSETS

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

    # EMPLOYEES

    cursor.execute("SELECT * FROM employees")

    employees = cursor.fetchall()

    # ASSIGNMENTS

    cursor.execute("""

        SELECT assignments.id,
               assignments.asset_id,
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

    # DASHBOARD COUNTS

    total_assets = len(assets)

    available_assets = len(
        [a for a in assets if a["status"] == "Available"]
    )

    assigned_assets = len(
        [a for a in assets if a["status"] == "Assigned"]
    )

    # CHART DATA

    chart_data = {
        "Available": available_assets,
        "Assigned": assigned_assets
    }

    conn.close()

    return render_template(
        "index.html",
        assets=assets,
        employees=employees,
        assignments=assignments,
        total_assets=total_assets,
        available_assets=available_assets,
        assigned_assets=assigned_assets,
        search=search,
        chart_data=chart_data
    )


# ADD ASSET

@app.route("/add", methods=["POST"])
def add_asset():

    if not login_required():
        return redirect("/login")

    asset_name = request.form["asset_name"]
    asset_type = request.form["asset_type"]
    serial_number = request.form["serial_number"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # CHECK DUPLICATE SERIAL NUMBER

    cursor.execute(
        "SELECT * FROM assets WHERE serial_number=?",
        (serial_number,)
    )

    existing_asset = cursor.fetchone()

    if existing_asset:

        conn.close()

        return "Serial Number Already Exists"

    # INSERT ASSET

    cursor.execute("""

        INSERT INTO assets
        (
            asset_name,
            asset_type,
            serial_number,
            status
        )

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

    if not login_required():
        return redirect("/login")

    conn = get_db_connection()
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

    if not login_required():
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # DELETE ASSIGNMENTS

    cursor.execute(
        "DELETE FROM assignments WHERE asset_id=?",
        (asset_id,)
    )

    # DELETE ASSET

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

    if not login_required():
        return redirect("/login")

    employee_name = request.form["employee_name"]
    department = request.form["department"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO employees
        (
            employee_name,
            department
        )

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

    if not login_required():
        return redirect("/login")

    asset_id = request.form["asset_id"]
    employee_id = request.form["employee_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # CHECK ASSET

    cursor.execute(
        "SELECT * FROM assets WHERE id=?",
        (asset_id,)
    )

    asset = cursor.fetchone()

    if not asset:

        conn.close()

        return "Asset Not Found"

    # CHECK STATUS

    if asset["status"] == "Assigned":

        conn.close()

        return "Asset Already Assigned"

    # INSERT ASSIGNMENT

    cursor.execute("""

        INSERT INTO assignments
        (
            asset_id,
            employee_id
        )

        VALUES (?, ?)

    """, (
        asset_id,
        employee_id
    ))

    # UPDATE STATUS

    cursor.execute("""

        UPDATE assets

        SET status='Assigned'

        WHERE id=?

    """, (asset_id,))

    conn.commit()
    conn.close()

    return redirect("/")


# RETURN ASSET

@app.route("/return_asset/<int:assignment_id>")
def return_asset(assignment_id):

    if not login_required():
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    # GET ASSET ID

    cursor.execute("""

        SELECT asset_id
        FROM assignments
        WHERE id=?

    """, (assignment_id,))

    assignment = cursor.fetchone()

    if assignment:

        asset_id = assignment["asset_id"]

        # UPDATE STATUS

        cursor.execute("""

            UPDATE assets

            SET status='Available'

            WHERE id=?

        """, (asset_id,))

        # DELETE ASSIGNMENT

        cursor.execute("""

            DELETE FROM assignments
            WHERE id=?

        """, (assignment_id,))

        conn.commit()

    conn.close()

    return redirect("/")


# EXPORT ASSETS

@app.route("/export_assets")
def export_assets():

    if not login_required():
        return redirect("/login")

    conn = get_db_connection()
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

        ws.append([
            asset["id"],
            asset["asset_name"],
            asset["asset_type"],
            asset["serial_number"],
            asset["status"]
        ])

    filename = "assets_report.xlsx"

    wb.save(filename)

    return send_file(
        filename,
        as_attachment=True
    )


# EXPORT EMPLOYEES

@app.route("/export_employees")
def export_employees():

    if not login_required():
        return redirect("/login")

    conn = get_db_connection()
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

        ws.append([
            employee["id"],
            employee["employee_name"],
            employee["department"]
        ])

    filename = "employees_report.xlsx"

    wb.save(filename)

    return send_file(
        filename,
        as_attachment=True
    )


# RUN APPLICATION

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )