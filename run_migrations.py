import os
import mysql.connector

conn = mysql.connector.connect(
    host="mysql",
    user="root",
    password="root",
    database="fuzzy_saham"
)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) UNIQUE,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

files = sorted(os.listdir("migrations"))

for f in files:
    cur.execute("SELECT 1 FROM schema_migrations WHERE filename=%s", (f,))
    if cur.fetchone():
        continue

    with open(f"/database//migrations/{f}", "r") as sql:
        cur.execute(sql.read(), multi=True)

    cur.execute(
        "INSERT INTO schema_migrations (filename) VALUES (%s)", (f,)
    )
    conn.commit()
    print(f"Applied migration: {f}")

cur.close()
conn.close()
