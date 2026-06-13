import sqlite3

conn = sqlite3.connect('assets.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_name TEXT,
    department TEXT
)
''')

conn.commit()
conn.close()

print("Employees table created successfully")