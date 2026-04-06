import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "cinema_home.db"
conn = sqlite3.connect(db_path)
rows = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
).fetchall()

for row in rows:
    print(row[0])
