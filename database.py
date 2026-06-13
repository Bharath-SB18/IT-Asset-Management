import sqlite3

conn = sqlite3.connect('assets.db')

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_name TEXT,
    asset_type TEXT,
    serial_number TEXT,
    status TEXT
)
''')

conn.commit()
conn.close()

print("Assets table created successfully")