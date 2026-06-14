import sqlite3
from werkzeug.security import generate_password_hash

# =========================
# CONNECT DATABASE
# =========================
conn = sqlite3.connect('assets.db')
cursor = conn.cursor()


# =========================
# CREATE USERS TABLE
# =========================
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')


# =========================
# CREATE DEFAULT ADMIN USER (SECURE)
# =========================
admin_username = "admin"
admin_password = "admin123"

hashed_password = generate_password_hash(admin_password)

cursor.execute("""
INSERT OR IGNORE INTO users (username, password)
VALUES (?, ?)
""", (admin_username, hashed_password))


# =========================
# COMMIT AND CLOSE
# =========================
conn.commit()
conn.close()

print("Database initialized successfully with secure admin user")