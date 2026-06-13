import sqlite3

conn = sqlite3.connect('assets.db')
cursor = conn.cursor()

# Sample Assets
cursor.execute("""
INSERT INTO assets
(asset_name, asset_type, serial_number, status)
VALUES
('Dell Latitude 5420', 'Laptop', 'DL1001', 'Available')
""")

cursor.execute("""
INSERT INTO assets
(asset_name, asset_type, serial_number, status)
VALUES
('HP EliteBook', 'Laptop', 'HP1002', 'Available')
""")

# Sample Employees
cursor.execute("""
INSERT INTO employees
(employee_name, department)
VALUES
('Bharath', 'IT')
""")

cursor.execute("""
INSERT INTO employees
(employee_name, department)
VALUES
('Ravi', 'HR')
""")

conn.commit()
conn.close()

print("Sample Data Added Successfully")