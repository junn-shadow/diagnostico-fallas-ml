"""
conftest.py – Fixtures compartidas para la suite de tests.

La fixture ``in_memory_db`` crea una base de datos SQLite en memoria
y parchea ``get_connection`` tanto en connection.py como en repositories.py
para que todos los metodos del repositorio usen esa conexion temporal
durante el test, sin tocar el archivo real en disco.

NOTA TECNICA:
  repositories.py importa get_connection con:
      from app.database.connection import get_connection
  Eso crea una referencia local en el modulo. Hay que parchear esa
  referencia local (app.database.repositories.get_connection), no
  la original (app.database.connection.get_connection).

  Ademas, los metodos usan "with get_connection() as conn:", pero
  sqlite3.Connection no es un context manager por defecto en Python 3.10;
  si se abre y cierra la conexion en cada llamada con ":memory:", la BD
  desapareceria. Usamos una conexion persistente y la exponemos directamente.
"""
import sqlite3

import pytest

# Importar el modulo (no la funcion) para poder parchear la referencia interna
import app.database.repositories as repo_module


def _create_schema(conn: sqlite3.Connection) -> None:
    """Crea el esquema completo (incidents + raw_logs) en la conexion dada."""
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id     INTEGER,
            raw_log     TEXT,
            level       TEXT,
            event_template TEXT,
            is_anomaly  INTEGER,
            anomaly_score REAL,
            semantic_cluster INTEGER,
            root_cause  TEXT,
            recommendation TEXT,
            log_source  TEXT,
            run_id      TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS raw_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            line_id     INTEGER,
            timestamp   TEXT,
            level       TEXT,
            message     TEXT NOT NULL,
            source      TEXT,
            ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()


class _PersistentConn:
    """Envoltorio que hace que sqlite3.Connection funcione como context manager
    sin cerrar la conexion al salir del bloque 'with'.

    Esto es necesario porque repositories.py usa:
        with get_connection() as conn:
            ...
    y en Python 3.10 sqlite3.Connection.__exit__ hace commit/rollback
    pero NO cierra la conexion. Sin embargo, necesitamos que la misma
    instancia sea devuelta en cada llamada para que la BD en-memoria
    persista entre metodos del mismo test.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # Delegar todos los accesos al conn real
    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._conn.commit()
        else:
            self._conn.rollback()
        return False  # no suprimir excepciones


@pytest.fixture(scope="function")
def in_memory_db(monkeypatch):
    """Fixture que proporciona una BD SQLite en-memoria aislada por test.

    Parcha ``get_connection`` dentro de ``app.database.repositories`` para
    que todos los metodos de LogRepository usen esta conexion temporal.
    Al finalizar el test, la conexion se cierra automaticamente.

    Uso::

        def test_algo(in_memory_db):
            from app.database.repositories import LogRepository
            LogRepository.add_log(message="test")
            assert LogRepository.count() == 1
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_schema(conn)

    persistent = _PersistentConn(conn)

    # Parchear la referencia LOCAL dentro de repositories.py
    monkeypatch.setattr(repo_module, "get_connection", lambda: persistent)
    # Tambien parchear init_db para que no haga nada (esquema ya creado)
    monkeypatch.setattr(repo_module, "init_db", lambda: None)

    yield conn

    conn.close()
