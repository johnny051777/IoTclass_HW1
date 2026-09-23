import sqlite3
import os
from typing import List, Dict, Tuple, Optional

DB_NAME = "data.db"

def get_connection(db_path: str = DB_NAME) -> sqlite3.Connection:
    """Create and return a SQLite database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = DB_NAME) -> None:
    """Step 8 & 9: Create database and TemperatureForecasts table if not exists."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TemperatureForecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regionName TEXT NOT NULL,
                dataDate TEXT NOT NULL,
                mint REAL NOT NULL,
                maxt REAL NOT NULL,
                UNIQUE(regionName, dataDate)
            );
        """)
        conn.commit()
    print("Database and table 'TemperatureForecasts' initialized successfully.")

def insert_forecasts(records: List[Dict[str, any]], db_path: str = DB_NAME) -> int:
    """
    Step 8 & 20: Insert forecast records idempotently (ignore duplicates).
    Each dict in records: {'regionName': str, 'dataDate': str, 'mint': float, 'maxt': float}
    """
    inserted_count = 0
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for rec in records:
            cursor.execute("""
                INSERT OR IGNORE INTO TemperatureForecasts (regionName, dataDate, mint, maxt)
                VALUES (?, ?, ?, ?);
            """, (rec['regionName'], rec['dataDate'], float(rec['mint']), float(rec['maxt'])))
            if cursor.rowcount > 0:
                inserted_count += 1
        conn.commit()
    return inserted_count

def get_distinct_regions(db_path: str = DB_NAME) -> List[str]:
    """Step 10: SELECT DISTINCT regionName FROM TemperatureForecasts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName;")
        rows = cursor.fetchall()
        return [row["regionName"] for row in rows]

def query_by_region(region_name: str, db_path: str = DB_NAME) -> List[Dict[str, any]]:
    """Step 10: SELECT * FROM TemperatureForecasts WHERE regionName = ?."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, regionName, dataDate, mint, maxt 
            FROM TemperatureForecasts 
            WHERE regionName = ? 
            ORDER BY dataDate ASC;
        """, (region_name,))
        return [dict(row) for row in cursor.fetchall()]

def query_all(db_path: str = DB_NAME) -> List[Dict[str, any]]:
    """SELECT * FROM TemperatureForecasts ORDER BY dataDate, regionName."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, regionName, dataDate, mint, maxt FROM TemperatureForecasts ORDER BY dataDate ASC;")
        return [dict(row) for row in cursor.fetchall()]

if __name__ == "__main__":
    # Test database setup & queries (Step 10 Verification)
    init_db()
    print("Distinct regions:", get_distinct_regions())
