import sqlite3

conn = sqlite3.connect("cinema_home.db")
rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
).fetchall()

for row in rows:
    print(row[0])
