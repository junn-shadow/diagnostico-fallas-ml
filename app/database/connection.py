import sqlite3
from pathlib import Path

from app.config.paths import DATABASE_PATH


def get_connection(path: str | Path = DATABASE_PATH):
    conn = sqlite3.connect(Path(path), timeout=30.0)
    # Habilitar modo WAL para concurrencia profesional y evitar bloqueos (database is locked)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
    except Exception:
        pass
    return conn
