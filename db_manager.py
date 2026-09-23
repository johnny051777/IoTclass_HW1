import sqlite3
import os
from typing import List, Dict, Tuple, Optional

# On Vercel serverless runtime, only /tmp is writable
def get_db_path() -> str:
    if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
        return "/tmp/data.db"
    return os.environ.get("DB_PATH", "data.db")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a SQLite database connection."""
    target_path = db_path if db_path else get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Create database, TemperatureForecasts table, and WeatherAlerts table."""
    target_path = db_path if db_path else get_db_path()
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        
        # TemperatureForecasts table with wx, pop, ci
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TemperatureForecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regionName TEXT NOT NULL,
                dataDate TEXT NOT NULL,
                mint REAL NOT NULL,
                maxt REAL NOT NULL,
                wx TEXT DEFAULT '多雲',
                pop REAL DEFAULT 0,
                ci TEXT DEFAULT '舒適',
                UNIQUE(regionName, dataDate)
            );
        """)
        
        # Schema migration check
        cursor.execute("PRAGMA table_info(TemperatureForecasts);")
        existing_cols = [col["name"] for col in cursor.fetchall()]
        if "wx" not in existing_cols:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN wx TEXT DEFAULT '多雲';")
        if "pop" not in existing_cols:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN pop REAL DEFAULT 0;")
        if "ci" not in existing_cols:
            cursor.execute("ALTER TABLE TemperatureForecasts ADD COLUMN ci TEXT DEFAULT '舒適';")

        # WeatherAlerts table for CWA weather warnings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS WeatherAlerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                event TEXT NOT NULL,
                description TEXT,
                areaName TEXT,
                updatedTime TEXT,
                UNIQUE(headline, areaName)
            );
        """)
        conn.commit()

def insert_forecasts(records: List[Dict[str, any]], db_path: Optional[str] = None) -> int:
    """Insert or replace forecast records idempotently with wx, pop, and ci."""
    target_path = db_path if db_path else get_db_path()
    inserted_count = 0
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        for rec in records:
            cursor.execute("""
                INSERT INTO TemperatureForecasts (regionName, dataDate, mint, maxt, wx, pop, ci)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(regionName, dataDate) DO UPDATE SET
                    mint=excluded.mint,
                    maxt=excluded.maxt,
                    wx=excluded.wx,
                    pop=excluded.pop,
                    ci=excluded.ci;
            """, (
                rec['regionName'], 
                rec['dataDate'], 
                float(rec['mint']), 
                float(rec['maxt']),
                rec.get('wx', '多雲'),
                float(rec.get('pop', 0)),
                rec.get('ci', '舒適')
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
        conn.commit()
    return inserted_count

def insert_alerts(alerts: List[Dict[str, any]], db_path: Optional[str] = None) -> None:
    """Insert active weather warnings into WeatherAlerts table."""
    target_path = db_path if db_path else get_db_path()
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM WeatherAlerts;")
        for a in alerts:
            cursor.execute("""
                INSERT OR IGNORE INTO WeatherAlerts (headline, event, description, areaName, updatedTime)
                VALUES (?, ?, ?, ?, ?);
            """, (a['headline'], a['event'], a.get('description', ''), a.get('areaName', '全台'), a.get('updatedTime', '')));
        conn.commit()

def query_alerts(db_path: Optional[str] = None) -> List[Dict[str, any]]:
    """Query active weather alerts."""
    target_path = db_path if db_path else get_db_path()
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT headline, event, description, areaName, updatedTime FROM WeatherAlerts;")
        return [dict(row) for row in cursor.fetchall()]

def query_all(db_path: Optional[str] = None) -> List[Dict[str, any]]:
    """SELECT all records including wx, pop, and ci."""
    target_path = db_path if db_path else get_db_path()
    with get_connection(target_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, regionName, dataDate, mint, maxt, wx, pop, ci FROM TemperatureForecasts ORDER BY dataDate ASC;")
        return [dict(row) for row in cursor.fetchall()]

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {get_db_path()}")
