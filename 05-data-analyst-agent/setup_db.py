"""
Create and populate the sample SQLite sales database.
Run: python setup_db.py
"""

import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "./sales.db"

REGIONS = ["APAC", "EMEA", "Americas", "South Asia"]
PRODUCTS = ["Laptop", "Monitor", "Keyboard", "Headset", "Webcam", "Docking Station"]
CATEGORIES = {"Laptop": "Computing", "Monitor": "Display", "Keyboard": "Peripherals",
               "Headset": "Audio", "Webcam": "Peripherals", "Docking Station": "Computing"}
SEGMENTS = ["Enterprise", "SMB", "Consumer"]

random.seed(42)


def generate_rows(n: int = 500) -> list[tuple]:
    rows = []
    start = date(2023, 1, 1)
    for i in range(n):
        sale_date = start + timedelta(days=random.randint(0, 364))
        product = random.choice(PRODUCTS)
        region = random.choice(REGIONS)
        segment = random.choice(SEGMENTS)
        units = random.randint(1, 50)
        base_price = {"Laptop": 1200, "Monitor": 350, "Keyboard": 80,
                      "Headset": 150, "Webcam": 90, "Docking Station": 220}[product]
        revenue = round(units * base_price * random.uniform(0.85, 1.15), 2)
        returns = random.randint(0, max(1, units // 10))
        rows.append((sale_date.isoformat(), region, product, CATEGORIES[product],
                      revenue, units, returns, segment))
    return rows


def setup():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS sales")
    conn.execute("""
        CREATE TABLE sales (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            region          TEXT NOT NULL,
            product         TEXT NOT NULL,
            category        TEXT NOT NULL,
            revenue         REAL NOT NULL,
            units_sold      INTEGER NOT NULL,
            returns         INTEGER NOT NULL,
            customer_segment TEXT NOT NULL
        )
    """)
    rows = generate_rows(500)
    conn.executemany(
        "INSERT INTO sales (date, region, product, category, revenue, units_sold, returns, customer_segment) VALUES (?,?,?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with {len(rows)} rows.")


if __name__ == "__main__":
    setup()
