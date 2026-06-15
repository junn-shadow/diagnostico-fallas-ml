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


def save_incidents(logs: pd.DataFrame, log_source: str = "unknown", run_id: str | None = None) -> int:
    init_db()
    incidents = logs[logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])].copy()
    if incidents.empty:
        return 0
    incidents["is_anomaly"] = incidents["is_anomaly"].astype(int)
    incidents["log_source"] = log_source
    incidents["run_id"] = run_id or "unknown"
    
    with get_connection() as conn:
        incidents[INCIDENT_COLUMNS].to_sql("incidents", conn, if_exists="append", index=False)
    return len(incidents)


def list_incidents(run_id: str | None = None, limit: int = 200) -> pd.DataFrame:
    init_db()
    with get_connection() as conn:
        if run_id:
            return pd.read_sql_query(
                "SELECT * FROM incidents WHERE run_id = ? ORDER BY line_id ASC LIMIT ?",
                conn,
                params=(run_id, limit),
            )
        else:
            return pd.read_sql_query(
                "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?",
                conn,
                params=(limit,),
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
    with get_connection() as conn:
        conn.execute("DELETE FROM incidents WHERE run_id = ?", (run_id,))
        conn.commit()


def search_all_incidents(query: str, limit: int = 500) -> pd.DataFrame:
    """
    Realiza una búsqueda global por palabra clave sobre todos los incidentes del historial.
    """
    init_db()
    with get_connection() as conn:
        q = f"%{query}%"
        return pd.read_sql_query(
            """
            SELECT * FROM incidents 
            WHERE raw_log LIKE ? OR root_cause LIKE ? OR recommendation LIKE ? OR log_source LIKE ?
            ORDER BY created_at DESC LIMIT ?
            """,
            conn,
            params=(q, q, q, q, limit)
        )


def get_incident_summary(run_id: str | None = None) -> dict:
    """
    Retorna un diccionario con estadísticas agregadas de los incidentes.
    """
    init_db()
    with get_connection() as conn:
        if run_id:
            df = pd.read_sql_query(
                "SELECT level, is_anomaly FROM incidents WHERE run_id = ?",
                conn,
                params=(run_id,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT level, is_anomaly FROM incidents",
                conn
            )
            
        if df.empty:
            return {
                "total": 0,
                "anomalies": 0,
                "errors": 0,
                "severity_counts": {}
            }
            
        total = len(df)
        anomalies = int(df["is_anomaly"].sum())
        errors = int(df["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())
        severity_counts = df["level"].value_counts().to_dict()
        
        return {
            "total": total,
            "anomalies": anomalies,
            "errors": errors,
            "severity_counts": severity_counts
        }

