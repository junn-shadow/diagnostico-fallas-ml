import pandas as pd
import io
from app.database.connection import get_connection

def generate_report(format: str = "csv", run_id: str | None = None) -> bytes:
    """
    Obtiene los datos de la base de datos para una ejecución específica (o todos)
    y devuelve un flujo de bytes en el formato solicitado ('csv', 'json', 'xlsx').
    """
    with get_connection() as conn:
        if run_id:
            df = pd.read_sql_query(
                "SELECT * FROM incidents WHERE run_id = ? ORDER BY line_id ASC",
                conn,
                params=(run_id,)
            )
        else:
            df = pd.read_sql_query(
                "SELECT * FROM incidents ORDER BY created_at DESC",
                conn
            )
            
    if df.empty:
        # Retornar bytes vacíos o un CSV con cabeceras si no hay datos
        if format == "json":
            return b"[]"
        elif format == "xlsx":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl" if "openpyxl" in globals() else "xlsxwriter") as writer:
                pd.DataFrame().to_excel(writer, index=False)
            return buffer.getvalue()
        else:
            return b"No data available"

    if format == "csv":
        return df.to_csv(index=False).encode("utf-8")
    elif format == "json":
        return df.to_json(orient="records", force_ascii=False).encode("utf-8")
    elif format == "xlsx":
        try:
            buffer = io.BytesIO()
            # Usar openpyxl, si no está instalado, fallará con ImportError
            df.to_excel(buffer, index=False, engine="openpyxl")
            return buffer.getvalue()
        except ImportError:
            # Fallback a CSV si openpyxl no está instalado
            return df.to_csv(index=False).encode("utf-8")
            
    raise ValueError(f"Formato no soportado: {format}")
