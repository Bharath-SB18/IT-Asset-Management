import sqlite3

conn = sqlite3.connect('assets.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER,
    employee_id INTEGER,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("Assignments table created successfully")