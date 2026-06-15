from app.database.connection import get_connection


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id INTEGER,
                raw_log TEXT,
                level TEXT,
                event_template TEXT,
                is_anomaly INTEGER,
                anomaly_score REAL,
                semantic_cluster INTEGER,
                root_cause TEXT,
                recommendation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        
        # Migración automática retrocompatible para añadir columnas extras
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(incidents)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "log_source" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN log_source TEXT")
        if "run_id" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN run_id TEXT")
        conn.commit()

