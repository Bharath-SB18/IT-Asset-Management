import sqlite3

conn = sqlite3.connect('assets.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute("""
INSERT OR IGNORE INTO users
(username, password)
VALUES
('admin', 'admin123')
""")

conn.commit()
conn.close()

print("User table created")