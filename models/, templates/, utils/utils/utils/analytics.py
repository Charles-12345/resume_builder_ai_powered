import sqlite3
from datetime import datetime

DB_PATH = "analytics.db"

def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                event TEXT NOT NULL,
                template TEXT,
                amount REAL,
                meta TEXT
            )
        """)
        con.commit()

def log_event(event: str, template: str | None = None, amount: float | None = None, meta: str | None = None) -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT INTO events (ts, event, template, amount, meta) VALUES (?, ?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), event, template, amount, meta),
        )
        con.commit()

def fetch_events():
    with sqlite3.connect(DB_PATH) as con:
        return con.execute(
            "SELECT ts, event, template, amount, meta FROM events ORDER BY ts DESC"
        ).fetchall()
