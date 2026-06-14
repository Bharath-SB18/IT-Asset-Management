import sqlite3

from werkzeug.security import generate_password_hash


# DATABASE CONNECTION

conn = sqlite3.connect("assets.db")

cursor = conn.cursor()


# USERS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    username TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL

)

""")


# ASSETS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS assets (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asset_name TEXT NOT NULL,

    asset_type TEXT NOT NULL,

    serial_number TEXT UNIQUE NOT NULL,

    status TEXT NOT NULL

)

""")


# EMPLOYEES TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS employees (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    employee_name TEXT NOT NULL,

    department TEXT NOT NULL

)

""")


# ASSIGNMENTS TABLE

cursor.execute("""

CREATE TABLE IF NOT EXISTS assignments (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    asset_id INTEGER NOT NULL,

    employee_id INTEGER NOT NULL,

    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (asset_id) REFERENCES assets(id),

    FOREIGN KEY (employee_id) REFERENCES employees(id)

)

""")


# CREATE DEFAULT ADMIN USER

hashed_password = generate_password_hash("admin123")

cursor.execute("""

INSERT OR IGNORE INTO users (

    id,
    username,
    password

)

VALUES (?, ?, ?)

""", (

    1,
    "admin",
    hashed_password

))


# SAVE DATABASE

conn.commit()

conn.close()


print("===================================")
print(" Database Created Successfully ")
print("===================================")

print("Default Login Details")
print("------------------------------")
print("Username : admin")
print("Password : admin123")
print("------------------------------")