from pathlib import Path

from app.database.connection import get_connection


def get_db_path() -> Path:
    """Devuelve la ruta efectiva del archivo SQLite.

    Respeta la variable de entorno SQLITE_DB_PATH si está definida;
    de lo contrario usa DATABASE_PATH de paths.py (incidents.sqlite3).
    """
    from app.config.settings import SQLITE_DB_PATH
    from app.config.paths import DATABASE_PATH

    if SQLITE_DB_PATH:
        return Path(SQLITE_DB_PATH)
    return DATABASE_PATH


def init_db() -> None:
    """Crea o actualiza el esquema de la base de datos SQLite.

    Tablas gestionadas:
    - incidents: anomalías y errores detectados por el pipeline.
    - raw_logs:  todas las líneas de log ingeridas (base de conocimientos).
    """
    with get_connection() as conn:
        # ── Tabla incidents (pre-existente) ─────────────────────────────────
        conn.execute("""
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
            """)

        # Migración automática retrocompatible para añadir columnas extras
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(incidents)")
        columns = [row[1] for row in cursor.fetchall()]

        if "log_source" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN log_source TEXT")
        if "run_id" not in columns:
            cursor.execute("ALTER TABLE incidents ADD COLUMN run_id TEXT")

        # Crear índices para optimizar las consultas con gran volumen de datos
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_run_id ON incidents(run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_level ON incidents(level)")

        # ── Tabla raw_logs (nueva: base de conocimientos de logs crudos) ────
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id   INTEGER,
                timestamp TEXT,
                level     TEXT,
                message   TEXT NOT NULL,
                source    TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("PRAGMA table_info(raw_logs)")
        raw_cols = [row[1] for row in cursor.fetchall()]
        # Por si se necesitan columnas futuras (migración automática)
        if "source" not in raw_cols:
            cursor.execute("ALTER TABLE raw_logs ADD COLUMN source TEXT")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_logs_level ON raw_logs(level)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_logs_source ON raw_logs(source)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_logs_timestamp ON raw_logs(timestamp)"
        )

        conn.commit()

