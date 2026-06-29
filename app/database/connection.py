import sqlite3
from pathlib import Path

def get_connection(path: str | Path = None):
    if path is None:
        # Importación local para evitar dependencias circulares
        from app.database.sqlite_db import get_db_path
        path = get_db_path()
        
    conn = sqlite3.connect(Path(path), timeout=30.0)
    # Habilitar modo WAL para concurrencia profesional y evitar bloqueos (database is locked)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
    except Exception:
        pass
    return conn
