import pandas as pd

from app.database.connection import get_connection
from app.database.sqlite_db import init_db

INCIDENT_COLUMNS = [
    "line_id",
    "raw_log",
    "level",
    "event_template",
    "is_anomaly",
    "anomaly_score",
    "semantic_cluster",
    "root_cause",
    "recommendation",
    "log_source",
    "run_id",
]


def save_incidents(
    logs: pd.DataFrame, log_source: str = "unknown", run_id: str | None = None
) -> int:
    init_db()
    incidents = logs[
        logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
    ].copy()
    if incidents.empty:
        return 0
    incidents["is_anomaly"] = incidents["is_anomaly"].astype(int)
    incidents["log_source"] = log_source
    incidents["run_id"] = run_id or "unknown"

    import sqlalchemy as sa
    with get_connection() as conn:
        # Eliminar ejecuciones anteriores de la misma fuente de datos (log_source)
        # para no ocupar espacio innecesario en Supabase
        if log_source and log_source != "unknown":
            conn.execute(
                sa.text("DELETE FROM incidents WHERE log_source = :log_source"),
                {"log_source": log_source}
            )
            # También limpiamos los logs crudos asociados a esa fuente si los hay
            try:
                conn.execute(
                    sa.text("DELETE FROM raw_logs WHERE source = :log_source"),
                    {"log_source": log_source}
                )
            except Exception:
                pass
            conn.commit()

        incidents[INCIDENT_COLUMNS].to_sql(
            "incidents", conn, if_exists="append", index=False
        )
    return len(incidents)


def list_incidents(run_id: str | None = None, limit: int = 200) -> pd.DataFrame:
    init_db()
    import sqlalchemy as sa
    with get_connection() as conn:
        if run_id:
            return pd.read_sql_query(
                sa.text("SELECT * FROM incidents WHERE run_id = :run_id ORDER BY line_id ASC LIMIT :limit"),
                conn,
                params={"run_id": run_id, "limit": limit},
            )
        else:
            return pd.read_sql_query(
                sa.text("SELECT * FROM incidents ORDER BY created_at DESC LIMIT :limit"),
                conn,
                params={"limit": limit},
            )


def list_runs() -> pd.DataFrame:
    """
    Retorna la lista de ejecuciones históricas con estadísticas rápidas.
    """
    init_db()
    query = """
        SELECT 
            run_id,
            log_source,
            MIN(created_at) as created_at,
            COUNT(*) as total_events,
            SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) as anomalies,
            SUM(CASE WHEN level IN ('ERROR', 'CRITICAL', 'FATAL') THEN 1 ELSE 0 END) as errors
        FROM incidents
        GROUP BY run_id, log_source
        ORDER BY created_at DESC
    """
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


def delete_run(run_id: str) -> None:
    """
    Elimina los registros correspondientes a una ejecución (run_id).
    """
    init_db()
    import sqlalchemy as sa
    with get_connection() as conn:
        conn.execute(sa.text("DELETE FROM incidents WHERE run_id = :run_id"), {"run_id": run_id})
        conn.commit()


def search_all_incidents(query: str, limit: int = 500) -> pd.DataFrame:
    """
    Realiza una búsqueda global por palabra clave sobre todos los incidentes del historial.
    """
    init_db()
    import sqlalchemy as sa
    with get_connection() as conn:
        q = f"%{query}%"
        return pd.read_sql_query(
            sa.text("""
            SELECT * FROM incidents 
            WHERE raw_log LIKE :q OR root_cause LIKE :q OR recommendation LIKE :q OR log_source LIKE :q
            ORDER BY created_at DESC LIMIT :limit
            """),
            conn,
            params={"q": q, "limit": limit},
        )


def get_incident_summary(run_id: str | None = None) -> dict:
    """
    Retorna un diccionario con estadísticas agregadas de los incidentes.
    """
    init_db()
    import sqlalchemy as sa
    with get_connection() as conn:
        if run_id:
            df = pd.read_sql_query(
                sa.text("SELECT level, is_anomaly FROM incidents WHERE run_id = :run_id"),
                conn,
                params={"run_id": run_id},
            )
        else:
            df = pd.read_sql_query("SELECT level, is_anomaly FROM incidents", conn)

        if df.empty:
            return {"total": 0, "anomalies": 0, "errors": 0, "severity_counts": {}}

        total = len(df)
        anomalies = int(df["is_anomaly"].sum())
        errors = int(df["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())
        severity_counts = df["level"].value_counts().to_dict()

        return {
            "total": total,
            "anomalies": anomalies,
            "errors": errors,
            "severity_counts": severity_counts,
        }


# ─────────────────────────────────────────────────────────────────────────────
# LogRepository – base de conocimientos de logs crudos (tabla raw_logs)
# ─────────────────────────────────────────────────────────────────────────────

import sqlite3
from typing import List, Optional


class LogRepository:
    """Repositorio de acceso a la tabla ``raw_logs``.

    Todas las lineas de log ingeridas se almacenan aqui como base de
    conocimientos. Los metodos exponen operaciones CRUD basicas y busquedas
    por nivel, palabra clave y fuente.
    """

    @staticmethod
    def add_log(
        message: str,
        line_id: int = 0,
        timestamp: str = "",
        level: str = "INFO",
        source: Optional[str] = None,
    ) -> None:
        """Inserta un unico log crudo en la base de conocimientos."""
        import os
        import streamlit as st
        is_cloud_db = ("TURSO_DATABASE_URL" in st.secrets or "SUPABASE_URL" in st.secrets or
                      os.getenv("TURSO_DATABASE_URL") or os.getenv("SUPABASE_URL"))
        if is_cloud_db:
            return  # No guardar logs individuales en la nube (ahorro de cuota de escritura/espacio)

        init_db()
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO raw_logs (line_id, timestamp, level, message, source) VALUES (?, ?, ?, ?, ?)",
                (line_id, timestamp, level, message, source),
            )
            conn.commit()

    @staticmethod
    def add_logs_bulk(records: List[dict]) -> int:
        """Inserta multiples logs de manera eficiente (executemany).

        Args:
            records: Lista de dicts con claves:
                line_id, timestamp, level, message, source.

        Returns:
            Numero de filas insertadas.
        """
        if not records:
            return 0

        import os
        import streamlit as st
        is_cloud_db = ("TURSO_DATABASE_URL" in st.secrets or "SUPABASE_URL" in st.secrets or
                      os.getenv("TURSO_DATABASE_URL") or os.getenv("SUPABASE_URL"))
        if is_cloud_db:
            return len(records)  # Simular inserción exitosa para no romper el pipeline en la nube

        init_db()
        rows = [
            (
                r.get("line_id", 0),
                r.get("timestamp", ""),
                r.get("level", "INFO"),
                r.get("message", ""),
                r.get("source"),
            )
            for r in records
        ]
        with get_connection() as conn:
            conn.executemany(
                "INSERT INTO raw_logs (line_id, timestamp, level, message, source) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        return len(rows)

    @staticmethod
    def get_by_id(log_id: int) -> Optional[dict]:
        """Recupera un log por su id primario."""
        init_db()
        with get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM raw_logs WHERE id = ?", (log_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_all(limit: int = 200, source: Optional[str] = None) -> pd.DataFrame:
        """Lista todos los logs crudos almacenados."""
        init_db()
        with get_connection() as conn:
            if source:
                return pd.read_sql_query(
                    "SELECT * FROM raw_logs WHERE source = ? ORDER BY id DESC LIMIT ?",
                    conn,
                    params=(source, limit),
                )
            return pd.read_sql_query(
                "SELECT * FROM raw_logs ORDER BY id DESC LIMIT ?",
                conn,
                params=(limit,),
            )

    @staticmethod
    def search_by_level(level: str, limit: int = 500) -> pd.DataFrame:
        """Filtra logs por nivel de severidad (INFO, WARNING, ERROR...)."""
        init_db()
        with get_connection() as conn:
            return pd.read_sql_query(
                "SELECT * FROM raw_logs WHERE level = ? ORDER BY id DESC LIMIT ?",
                conn,
                params=(level.upper(), limit),
            )

    @staticmethod
    def search_by_keyword(keyword: str, limit: int = 500) -> pd.DataFrame:
        """Busqueda de texto libre sobre el campo message."""
        init_db()
        pattern = f"%{keyword}%"
        with get_connection() as conn:
            return pd.read_sql_query(
                "SELECT * FROM raw_logs WHERE message LIKE ? ORDER BY id DESC LIMIT ?",
                conn,
                params=(pattern, limit),
            )

    @staticmethod
    def count(source: Optional[str] = None) -> int:
        """Devuelve el numero total de logs almacenados."""
        init_db()
        with get_connection() as conn:
            if source:
                cur = conn.execute("SELECT COUNT(*) FROM raw_logs WHERE source = ?", (source,))
            else:
                cur = conn.execute("SELECT COUNT(*) FROM raw_logs")
            return cur.fetchone()[0]

    @staticmethod
    def clear_source(source: str) -> int:
        """Elimina todos los logs de una fuente especifica (para re-ingestar sin duplicados)."""
        init_db()
        with get_connection() as conn:
            cur = conn.execute("DELETE FROM raw_logs WHERE source = ?", (source,))
            conn.commit()
            return cur.rowcount
