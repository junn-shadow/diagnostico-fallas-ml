from pathlib import Path
import sqlalchemy as sa
from app.database.connection import get_connection


def get_db_path() -> Path:
    from app.config.settings import SQLITE_DB_PATH
    from app.config.paths import DATABASE_PATH
    if SQLITE_DB_PATH:
        return Path(SQLITE_DB_PATH)
    return DATABASE_PATH


def init_db() -> None:
    """Inicializa las tablas necesarias (soporta Turso y SQLite local)."""
    with get_connection() as conn:
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS raw_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id INTEGER,
                timestamp TEXT,
                level TEXT,
                message TEXT,
                source TEXT
            )
        """))
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                log_source TEXT,
                created_at TEXT,
                total_events INTEGER,
                anomalies INTEGER,
                errors INTEGER
            )
        """))
        conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                line_id INTEGER,
                raw_log TEXT,
                clean_log TEXT,
                level TEXT,
                event_template TEXT,
                is_anomaly BOOLEAN,
                anomaly_score REAL,
                semantic_cluster TEXT,
                root_cause TEXT,
                recommendation TEXT,
                log_source TEXT
            )
        """))
        conn.commit()
