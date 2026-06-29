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
    """Las tablas se crean directamente en Supabase, por lo que no inicializamos localmente."""
    pass


